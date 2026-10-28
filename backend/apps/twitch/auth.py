import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


def decode_part(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_extension_token(token):
    secret = getattr(settings, "TWITCH_EXTENSION_SECRET", "")
    if not secret or not token or len(token) > 8192:
        raise AuthenticationFailed("Twitch Extension authentication is not configured or the token is missing.")
    try:
        header_part, payload_part, signature_part = token.split(".")
        header = json.loads(decode_part(header_part))
        payload = json.loads(decode_part(payload_part))
        secret_bytes = base64.b64decode(secret + "=" * (-len(secret) % 4), validate=True)
        signing_input = f"{header_part}.{payload_part}".encode("ascii")
        expected = hmac.new(secret_bytes, signing_input, hashlib.sha256).digest()
        actual = decode_part(signature_part)
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise AuthenticationFailed("The Twitch Extension token is malformed.")
    if header.get("alg") != "HS256" or not hmac.compare_digest(expected, actual):
        raise AuthenticationFailed("The Twitch Extension token signature is invalid.")
    try:
        expiration = int(payload.get("exp", 0))
        channel_id = str(payload.get("channel_id", ""))
        opaque_user_id = str(payload.get("opaque_user_id", ""))
    except (TypeError, ValueError):
        raise AuthenticationFailed("The Twitch Extension token claims are invalid.")
    if expiration <= int(time.time()) or not channel_id.isdigit() or not opaque_user_id or payload.get("role") not in {"viewer", "broadcaster", "moderator"}:
        raise AuthenticationFailed("The Twitch Extension token is expired or has invalid claims.")
    return {"channel_id": channel_id, "opaque_user_id": opaque_user_id, "role": payload.get("role", "")}

import base64
import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.sessions.models import CreatorSession


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def signed_token(secret, exp=None):
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    claims = {"exp": exp or int(time.time()) + 60, "opaque_user_id": "U123", "channel_id": "98765", "role": "viewer"}
    payload = b64(json.dumps(claims).encode())
    content = f"{header}.{payload}".encode()
    key = base64.b64decode(secret)
    signature = b64(hmac.new(key, content, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


@override_settings(TWITCH_EXTENSION_SECRET="c2VjcmV0")
class TwitchExtensionApiTests(APITestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user(username="twitch-owner", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=owner, title="Live extension session", status="live", twitch_channel_id="98765")

    def test_signed_extension_token_resolves_only_live_channel_session(self):
        response = self.client.post("/api/twitch/extension/session/", {}, HTTP_X_TWITCH_EXTENSION_JWT=signed_token("c2VjcmV0"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["session_token"], str(self.session.public_token))

    def test_invalid_signature_is_rejected(self):
        response = self.client.post("/api/twitch/extension/session/", {}, HTTP_X_TWITCH_EXTENSION_JWT=signed_token("d3Jvbmc="))
        self.assertEqual(response.status_code, 403)

    def test_expired_token_is_rejected(self):
        response = self.client.post("/api/twitch/extension/session/", {}, HTTP_X_TWITCH_EXTENSION_JWT=signed_token("c2VjcmV0", int(time.time()) - 1))
        self.assertEqual(response.status_code, 403)


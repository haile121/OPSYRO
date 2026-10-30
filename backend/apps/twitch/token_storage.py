from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _fernet():
    key = getattr(settings, "TWITCH_TOKEN_ENCRYPTION_KEY", "")
    if not key:
        raise ImproperlyConfigured("Set TWITCH_TOKEN_ENCRYPTION_KEY before connecting Twitch.")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        raise ImproperlyConfigured("TWITCH_TOKEN_ENCRYPTION_KEY must be a valid Fernet key.")


def encrypt_token(token: str) -> str:
    if not token:
        return ""
    return _fernet().encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    try:
        return _fernet().decrypt(encrypted_token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError):
        raise ImproperlyConfigured("A stored Twitch token could not be decrypted; verify TWITCH_TOKEN_ENCRYPTION_KEY.")

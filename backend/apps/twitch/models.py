from django.conf import settings
from django.db import models

from .token_storage import decrypt_token, encrypt_token


class TwitchConnection(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="twitch_connection")
    twitch_user_id = models.CharField(max_length=32, unique=True)
    login = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128)
    profile_image_url = models.URLField(max_length=500, blank=True)
    encrypted_access_token = models.TextField()
    encrypted_refresh_token = models.TextField()
    scopes = models.JSONField(default=list, blank=True)
    token_expires_at = models.DateTimeField()
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_tokens(self, access_token: str, refresh_token: str) -> None:
        self.encrypted_access_token = encrypt_token(access_token)
        self.encrypted_refresh_token = encrypt_token(refresh_token)

    def get_access_token(self) -> str:
        return decrypt_token(self.encrypted_access_token)

    def get_refresh_token(self) -> str:
        return decrypt_token(self.encrypted_refresh_token)

    def __str__(self):
        return f"Twitch connection for {self.owner_id} ({self.login})"

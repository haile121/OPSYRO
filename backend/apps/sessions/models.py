import uuid

from django.conf import settings
from django.db import models


class CreatorSession(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        LIVE = "live", "Live"
        ENDED = "ended", "Ended"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="creator_sessions")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=500, blank=True)
    twitch_channel_id = models.CharField(max_length=32, blank=True, db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("owner", "created_at"), name="session_owner_created_idx")]

    def __str__(self):
        return f"{self.title} ({self.status})"


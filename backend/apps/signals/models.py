import uuid

from django.db import models

from apps.questions.models import QuestionCluster
from apps.sessions.models import CreatorSession


class AudienceSignal(models.Model):
    class Intent(models.TextChoices):
        QUESTION = "question", "Question"
        CURIOUS = "curious", "Curious"
        CONFUSED = "confused", "Confused"

    session = models.ForeignKey(CreatorSession, on_delete=models.CASCADE, related_name="signals")
    cluster = models.ForeignKey(QuestionCluster, null=True, blank=True, on_delete=models.SET_NULL, related_name="signals")
    participant_key = models.UUIDField()
    idempotency_key = models.UUIDField()
    region_x = models.DecimalField(max_digits=5, decimal_places=4)
    region_y = models.DecimalField(max_digits=5, decimal_places=4)
    region_key = models.CharField(max_length=32, blank=True)
    intent = models.CharField(max_length=12, choices=Intent.choices, default=Intent.QUESTION)
    question = models.CharField(max_length=240, blank=True)
    media_time_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("session", "participant_key", "idempotency_key"), name="unique_signal_idempotency")]
        indexes = [models.Index(fields=("session", "created_at"), name="signal_session_created_idx")]

    def __str__(self):
        return f"Signal for session {self.session_id}"

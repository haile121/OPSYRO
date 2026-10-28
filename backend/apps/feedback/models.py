import uuid

from django.db import models

from apps.responses.models import CreatorResponse


class ViewerFeedback(models.Model):
    response = models.ForeignKey(CreatorResponse, on_delete=models.CASCADE, related_name="feedback")
    participant_key = models.UUIDField()
    idempotency_key = models.UUIDField()
    helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("response", "participant_key"), name="unique_response_participant_feedback")]
        indexes = [models.Index(fields=("response", "created_at"), name="feedback_response_created_idx")]

    def __str__(self):
        return f"Feedback for response {self.response_id}"

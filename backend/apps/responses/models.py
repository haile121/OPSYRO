from django.conf import settings
from django.db import models

from apps.questions.models import QuestionCluster


class CreatorResponse(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    cluster = models.OneToOneField(QuestionCluster, on_delete=models.CASCADE, related_name="response")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audience_responses")
    text = models.CharField(max_length=2000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Response to {self.cluster_id} ({self.status})"

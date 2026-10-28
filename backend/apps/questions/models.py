from django.db import models

from apps.sessions.models import CreatorSession


class QuestionCluster(models.Model):
    session = models.ForeignKey(CreatorSession, on_delete=models.CASCADE, related_name="question_clusters")
    label = models.CharField(max_length=240)
    match_key = models.CharField(max_length=240)
    region_key = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        constraints = [models.UniqueConstraint(fields=("session", "region_key", "match_key"), name="unique_session_region_question_key")]

    def __str__(self):
        return self.label

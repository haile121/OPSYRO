from django.conf import settings
from django.db import models
from django.utils import timezone


class Experiment(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETE = "complete", "Complete"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="experiments")
    sessions = models.ManyToManyField("creator_sessions.CreatorSession", related_name="experiments", blank=True)
    name = models.CharField(max_length=120)
    hypothesis = models.CharField(max_length=500, blank=True)
    change = models.CharField(max_length=500, blank=True)
    outcome = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def start(self):
        if self.status == self.Status.PLANNED:
            self.status = self.Status.ACTIVE
            self.started_at = timezone.now()
            self.save(update_fields=("status", "started_at", "updated_at"))

    def complete(self):
        if self.status == self.Status.ACTIVE:
            self.status = self.Status.COMPLETE
            self.completed_at = timezone.now()
            self.save(update_fields=("status", "completed_at", "updated_at"))

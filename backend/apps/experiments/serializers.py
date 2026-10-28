from rest_framework import serializers

from apps.sessions.models import CreatorSession
from .models import Experiment


class ExperimentSerializer(serializers.ModelSerializer):
    session_ids = serializers.PrimaryKeyRelatedField(
        source="sessions", many=True, queryset=CreatorSession.objects.all(), required=False
    )

    class Meta:
        model = Experiment
        fields = ("id", "name", "hypothesis", "change", "outcome", "status", "session_ids", "created_at", "started_at", "completed_at", "updated_at")
        read_only_fields = ("id", "status", "created_at", "started_at", "completed_at", "updated_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("An experiment name is required.")
        return value

    def validate_session_ids(self, sessions):
        owner = self.context["request"].user
        if any(session.owner_id != owner.id for session in sessions):
            raise serializers.ValidationError("Experiments can only include your sessions.")
        return sessions


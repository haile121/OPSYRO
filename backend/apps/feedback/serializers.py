from rest_framework import serializers

from .models import ViewerFeedback


class FeedbackCreateSerializer(serializers.Serializer):
    session_token = serializers.UUIDField()
    cluster_id = serializers.IntegerField(min_value=1)
    participant_key = serializers.UUIDField()
    idempotency_key = serializers.UUIDField()
    helpful = serializers.BooleanField()


class ViewerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewerFeedback
        fields = ("id", "helpful", "created_at")
        read_only_fields = fields

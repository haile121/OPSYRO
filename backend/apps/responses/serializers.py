from rest_framework import serializers

from .models import CreatorResponse


class CreatorResponseSerializer(serializers.ModelSerializer):
    cluster_id = serializers.IntegerField()
    feedback_count = serializers.IntegerField(read_only=True, default=0)
    helpful_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = CreatorResponse
        fields = ("id", "cluster_id", "text", "status", "feedback_count", "helpful_count", "created_at", "updated_at", "published_at")
        read_only_fields = ("id", "status", "feedback_count", "helpful_count", "created_at", "updated_at", "published_at")

    def create(self, validated_data):
        validated_data.pop("cluster_id", None)
        return super().create(validated_data)

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A response is required.")
        return value

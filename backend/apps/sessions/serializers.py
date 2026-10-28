from rest_framework import serializers

from .models import CreatorSession


class CreatorSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorSession
        fields = ("id", "title", "description", "twitch_channel_id", "status", "public_token", "created_at", "started_at", "ended_at")
        read_only_fields = ("id", "status", "public_token", "created_at", "started_at", "ended_at")

    def validate_twitch_channel_id(self, value):
        value = value.strip()
        if value and not value.isdigit():
            raise serializers.ValidationError("Enter the numeric Twitch channel ID.")
        return value

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A session title is required.")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.status != CreatorSession.Status.DRAFT:
            raise serializers.ValidationError("Only draft sessions can be edited.")
        return attrs



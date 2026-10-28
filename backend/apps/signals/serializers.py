from rest_framework import serializers

from .models import AudienceSignal


class SignalCreateSerializer(serializers.Serializer):
    session_token = serializers.UUIDField()
    participant_key = serializers.UUIDField()
    idempotency_key = serializers.UUIDField()
    region_x = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1)
    region_y = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1)
    region_key = serializers.RegexField(r"^[a-zA-Z0-9_-]{0,32}$", required=False, allow_blank=True, default="")
    intent = serializers.ChoiceField(choices=AudienceSignal.Intent.choices, default=AudienceSignal.Intent.QUESTION)
    question = serializers.CharField(max_length=240, required=False, allow_blank=True, default="", trim_whitespace=True)
    media_time_seconds = serializers.IntegerField(min_value=0, required=False, allow_null=True, default=None)

    def validate(self, attrs):
        attrs["question"] = attrs["question"].strip()
        if not attrs["question"] and not attrs["region_key"]:
            raise serializers.ValidationError("Choose a point of interest or add a question.")
        return attrs


class AudienceSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudienceSignal
        fields = ("id", "cluster_id", "region_x", "region_y", "region_key", "intent", "question", "media_time_seconds", "created_at")
        read_only_fields = fields

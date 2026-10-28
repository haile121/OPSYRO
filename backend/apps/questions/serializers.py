from rest_framework import serializers

from .models import QuestionCluster


class QuestionClusterSerializer(serializers.ModelSerializer):
    signal_count = serializers.IntegerField(read_only=True)
    example_questions = serializers.SerializerMethodField()
    creator_response = serializers.SerializerMethodField()

    class Meta:
        model = QuestionCluster
        fields = ("id", "label", "region_key", "signal_count", "example_questions", "creator_response", "created_at", "updated_at")
        read_only_fields = fields

    def get_example_questions(self, cluster):
        return list(cluster.signals.exclude(question="").order_by("created_at").values_list("question", flat=True)[:5])

    def get_creator_response(self, cluster):
        response = getattr(cluster, "response", None)
        if response is None:
            return None
        feedback = response.feedback.all()
        return {
            "id": response.id,
            "text": response.text,
            "status": response.status,
            "published_at": response.published_at,
            "feedback_count": feedback.count(),
            "helpful_count": feedback.filter(helpful=True).count(),
        }

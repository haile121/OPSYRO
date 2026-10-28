from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.questions.models import QuestionCluster
from apps.sessions.events import publish_session_event
from apps.sessions.models import CreatorSession
from .models import CreatorResponse
from .serializers import CreatorResponseSerializer


class CreatorResponseViewSet(viewsets.ModelViewSet):
    serializer_class = CreatorResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return CreatorResponse.objects.filter(cluster__session__owner=self.request.user).annotate(
            feedback_count=Count("feedback"), helpful_count=Count("feedback", filter=Q(feedback__helpful=True))
        ).select_related("cluster", "cluster__session")

    def perform_create(self, serializer):
        cluster = QuestionCluster.objects.filter(
            pk=serializer.validated_data["cluster_id"],
            session__owner=self.request.user,
            session__status=CreatorSession.Status.LIVE,
        ).first()
        if cluster is None:
            raise ValidationError({"cluster_id": "Question group is unavailable or its session is not live."})
        if CreatorResponse.objects.filter(cluster=cluster).exists():
            raise ValidationError({"cluster_id": "A response already exists for this question group."})
        serializer.save(cluster=cluster, creator=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.status != CreatorResponse.Status.DRAFT:
            raise ValidationError("Published responses cannot be edited.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        with transaction.atomic():
            response = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if response.status != CreatorResponse.Status.DRAFT:
                raise ValidationError({"status": "Only a draft response can be published."})
            response.status = CreatorResponse.Status.PUBLISHED
            response.published_at = timezone.now()
            response.save(update_fields=("status", "published_at", "updated_at"))
        publish_session_event(response.cluster.session_id, "response_created", {
            "response_id": response.id,
            "cluster_id": response.cluster_id,
            "status": response.status,
        })
        return Response(self.get_serializer(response).data)

    @action(detail=True, methods=["get"])
    def feedback(self, request, pk=None):
        response = self.get_object()
        return Response({
            "response_id": response.id,
            "feedback_count": response.feedback_count,
            "helpful_count": response.helpful_count,
        })

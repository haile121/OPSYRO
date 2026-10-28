from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.responses.models import CreatorResponse
from apps.sessions.events import publish_session_event
from apps.sessions.models import CreatorSession
from .models import ViewerFeedback
from .serializers import FeedbackCreateSerializer


class PublicResponsesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, session_token):
        session = CreatorSession.objects.filter(public_token=session_token).first()
        if session is None:
            raise NotFound("This audience session is unavailable.")
        responses = CreatorResponse.objects.filter(cluster__session=session, status=CreatorResponse.Status.PUBLISHED).annotate(
            feedback_count=Count("feedback"), helpful_count=Count("feedback", filter=Q(feedback__helpful=True))
        ).select_related("cluster")
        return Response({"title": session.title, "status": session.status, "responses": [
            {"id": item.id, "cluster_id": item.cluster_id, "question": item.cluster.label, "text": item.text,
             "feedback_count": item.feedback_count, "helpful_count": item.helpful_count, "published_at": item.published_at}
            for item in responses
        ]})


class FeedbackSubmitView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "audience_feedback"

    def post(self, request):
        serializer = FeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        session = CreatorSession.objects.filter(public_token=values["session_token"]).first()
        if session is None:
            raise NotFound("This audience session is unavailable.")
        creator_response = CreatorResponse.objects.filter(
            cluster_id=values["cluster_id"], cluster__session=session, status=CreatorResponse.Status.PUBLISHED
        ).first()
        if creator_response is None:
            raise NotFound("This creator response is unavailable.")
        existing = ViewerFeedback.objects.filter(response=creator_response, participant_key=values["participant_key"]).first()
        if existing:
            return self.existing_result(creator_response, existing, values["idempotency_key"])
        try:
            with transaction.atomic():
                ViewerFeedback.objects.create(response=creator_response, participant_key=values["participant_key"], idempotency_key=values["idempotency_key"], helpful=values["helpful"])
        except IntegrityError:
            existing = ViewerFeedback.objects.filter(response=creator_response, participant_key=values["participant_key"]).first()
            if existing is None:
                raise
            return self.existing_result(creator_response, existing, values["idempotency_key"])
        result = self.result(creator_response, False, status.HTTP_201_CREATED)
        publish_session_event(session.id, "feedback_updated", result.data)
        return result

    @classmethod
    def existing_result(cls, creator_response, existing, idempotency_key):
        if existing.idempotency_key != idempotency_key:
            raise ValidationError({"detail": "Feedback was already recorded for this response."})
        return cls.result(creator_response, True, status.HTTP_200_OK)

    @staticmethod
    def result(creator_response, duplicate, response_status):
        totals = creator_response.feedback.aggregate(
            feedback_count=Count("id"), helpful_count=Count("id", filter=Q(helpful=True))
        )
        return Response({"response_id": creator_response.id, "duplicate": duplicate, **totals}, status=response_status)

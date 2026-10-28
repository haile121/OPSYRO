from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.questions.services import cluster_for_question
from apps.sessions.models import CreatorSession
from apps.sessions.events import publish_session_event
from .models import AudienceSignal
from .serializers import AudienceSignalSerializer, SignalCreateSerializer


class SignalSubmitView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "audience_signal"

    def post(self, request):
        payload = SignalCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        session = CreatorSession.objects.filter(public_token=values["session_token"], status=CreatorSession.Status.LIVE).first()
        if session is None:
            raise NotFound("This audience session is unavailable.")
        existing = AudienceSignal.objects.filter(session=session, participant_key=values["participant_key"], idempotency_key=values["idempotency_key"]).first()
        if existing:
            return Response({"signal": AudienceSignalSerializer(existing).data, "duplicate": True}, status=status.HTTP_200_OK)
        cluster = cluster_for_question(session, values["question"], values["region_key"]) if values["question"] else None
        try:
            with transaction.atomic():
                signal = AudienceSignal.objects.create(session=session, cluster=cluster, **{key: value for key, value in values.items() if key not in {"session_token", "participant_key", "idempotency_key"}}, participant_key=values["participant_key"], idempotency_key=values["idempotency_key"])
        except IntegrityError:
            signal = AudienceSignal.objects.filter(session=session, participant_key=values["participant_key"], idempotency_key=values["idempotency_key"]).first()
            if signal is None:
                raise
            return Response({"signal": AudienceSignalSerializer(signal).data, "duplicate": True}, status=status.HTTP_200_OK)
        serialized = AudienceSignalSerializer(signal).data
        publish_session_event(session.id, "signal_created", {"signal": serialized})
        if cluster:
            publish_session_event(session.id, "cluster_updated", {"cluster_id": cluster.id, "label": cluster.label, "signal_count": cluster.signals.count()})
        return Response({"signal": serialized, "duplicate": False}, status=status.HTTP_201_CREATED)

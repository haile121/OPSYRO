from collections import Counter

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.feedback.models import ViewerFeedback
from apps.questions.models import QuestionCluster
from apps.questions.serializers import QuestionClusterSerializer
from apps.responses.models import CreatorResponse
from apps.signals.models import AudienceSignal
from apps.signals.serializers import AudienceSignalSerializer
from .events import publish_session_event
from .models import CreatorSession
from .serializers import CreatorSessionSerializer


class CreatorSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CreatorSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return CreatorSession.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        with transaction.atomic():
            session = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if session.status != CreatorSession.Status.DRAFT:
                raise ValidationError({"status": "Only a draft session can be started."})
            session.status = CreatorSession.Status.LIVE
            session.started_at = timezone.now()
            session.save(update_fields=("status", "started_at"))
        publish_session_event(session.id, "session_status_changed", {"status": session.status})
        return Response(self.get_serializer(session).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        with transaction.atomic():
            session = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if session.status != CreatorSession.Status.LIVE:
                raise ValidationError({"status": "Only a live session can be ended."})
            session.status = CreatorSession.Status.ENDED
            session.ended_at = timezone.now()
            session.save(update_fields=("status", "ended_at"))
        publish_session_event(session.id, "session_status_changed", {"status": session.status})
        return Response(self.get_serializer(session).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def signals(self, request, pk=None):
        session = self.get_object()
        queryset = AudienceSignal.objects.filter(session=session).select_related("cluster")
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(AudienceSignalSerializer(page, many=True).data)

    @action(detail=True, methods=["get"])
    def questions(self, request, pk=None):
        session = self.get_object()
        clusters = QuestionCluster.objects.filter(session=session).select_related("response").prefetch_related("response__feedback").annotate(signal_count=Count("signals")).filter(signal_count__gt=0)
        return Response(QuestionClusterSerializer(clusters, many=True).data)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        session = self.get_object()
        feedback_totals = ViewerFeedback.objects.filter(response__cluster__session=session).aggregate(
            total=Count("id"), helpful=Count("id", filter=Q(helpful=True))
        )
        return Response({
            "session_id": session.id,
            "signal_count": AudienceSignal.objects.filter(session=session).count(),
            "question_groups": QuestionCluster.objects.filter(session=session, signals__isnull=False).distinct().count(),
            "published_responses": CreatorResponse.objects.filter(cluster__session=session, status=CreatorResponse.Status.PUBLISHED).count(),
            "feedback_count": feedback_totals["total"],
            "helpful_feedback_count": feedback_totals["helpful"],
        })

    @action(detail=True, methods=["get"])
    def attention(self, request, pk=None):
        session = self.get_object()
        points = AudienceSignal.objects.filter(session=session).values_list("region_x", "region_y", "region_key")
        cells, regions = Counter(), Counter()
        for x, y, region_key in points.iterator():
            cells[(min(int(float(x) * 10), 9), min(int(float(y) * 10), 9))] += 1
            if region_key:
                regions[region_key] += 1
        return Response({
            "grid_size": 10,
            "signal_count": sum(cells.values()),
            "cells": [{"x": x, "y": y, "count": count} for (x, y), count in sorted(cells.items())],
            "region_summary": [{"region_key": key, "count": count} for key, count in regions.most_common()],
        })

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Experiment
from .serializers import ExperimentSerializer


class ExperimentViewSet(viewsets.ModelViewSet):
    serializer_class = ExperimentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return Experiment.objects.filter(owner=self.request.user).prefetch_related("sessions")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        experiment = self.get_object()
        if experiment.status != Experiment.Status.PLANNED:
            return Response({"detail": "Only a planned experiment can be started."}, status=status.HTTP_400_BAD_REQUEST)
        experiment.start()
        return Response(self.get_serializer(experiment).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        experiment = self.get_object()
        if experiment.status != Experiment.Status.ACTIVE:
            return Response({"detail": "Only an active experiment can be completed."}, status=status.HTTP_400_BAD_REQUEST)
        experiment.complete()
        return Response(self.get_serializer(experiment).data)

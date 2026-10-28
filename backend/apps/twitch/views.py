from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.sessions.models import CreatorSession
from .auth import verify_extension_token


class ExtensionSessionView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "twitch_extension_session"

    def post(self, request):
        token = request.headers.get("X-Twitch-Extension-Jwt", "")
        claims = verify_extension_token(token)
        session = CreatorSession.objects.filter(
            status=CreatorSession.Status.LIVE,
            twitch_channel_id=claims["channel_id"],
        ).order_by("-started_at").first()
        if not session:
            raise NotFound("There is no live OPSYRO session for this Twitch channel.")
        return Response({"session_token": str(session.public_token), "title": session.title}, status=status.HTTP_200_OK)

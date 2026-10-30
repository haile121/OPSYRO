from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok", "service": "opsyro-api", "stage": "creator-workspace"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/v1/auth/twitch/", include("apps.twitch.oauth_urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/sessions/", include("apps.sessions.urls")),
    path("api/signals/", include("apps.signals.urls")),
    path("api/responses/", include("apps.responses.urls")),
    path("api/feedback/", include("apps.feedback.urls")),
    path("api/experiments/", include("apps.experiments.urls")),
    path("api/twitch/", include("apps.twitch.urls")),
]

from django.urls import path
from .views import ExtensionSessionView

urlpatterns = [path("extension/session/", ExtensionSessionView.as_view(), name="twitch-extension-session")]

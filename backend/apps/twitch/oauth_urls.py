from django.urls import path

from .oauth_views import TwitchConnectionStatusView, TwitchOAuthAuthorizeView, TwitchOAuthCallbackView

urlpatterns = [
    path("authorize/", TwitchOAuthAuthorizeView.as_view(), name="twitch-oauth-authorize"),
    path("callback", TwitchOAuthCallbackView.as_view(), name="twitch-oauth-callback"),
    path("status/", TwitchConnectionStatusView.as_view(), name="twitch-oauth-status"),
]

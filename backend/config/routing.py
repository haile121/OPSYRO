from django.urls import re_path

from apps.sessions.consumers import CreatorSessionConsumer

websocket_urlpatterns = [
    re_path(r"^ws/sessions/(?P<session_id>\d+)/$", CreatorSessionConsumer.as_asgi()),
]

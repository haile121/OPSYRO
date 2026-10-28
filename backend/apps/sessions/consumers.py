from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .events import session_group_name
from .models import CreatorSession


class CreatorSessionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        if not await self.can_access_session(user.pk, self.session_id):
            await self.close(code=4404)
            return
        self.group_name = session_group_name(self.session_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Creator sockets receive server notifications only.
        await self.close(code=1008)

    async def signal_created(self, event):
        await self.send_json(event["payload"])

    async def cluster_updated(self, event):
        await self.send_json(event["payload"])

    async def response_created(self, event):
        await self.send_json(event["payload"])

    async def feedback_updated(self, event):
        await self.send_json(event["payload"])

    async def session_status_changed(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def can_access_session(self, user_id, session_id):
        return CreatorSession.objects.filter(pk=session_id, owner_id=user_id).exists()

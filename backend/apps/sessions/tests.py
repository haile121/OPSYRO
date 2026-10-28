from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase
from rest_framework.test import APITestCase

from apps.sessions.events import session_group_name
from apps.sessions.models import CreatorSession
from config.asgi import application


class CreatorSessionApiTests(APITestCase):
    def setUp(self):
        users = get_user_model().objects
        self.owner = users.create_user(username="owner", password="RiverGlass!308")
        self.other = users.create_user(username="other", password="RiverGlass!308")

    def test_sessions_require_authentication(self):
        response = self.client.post("/api/sessions/", {"title": "A stream"}, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_owner_can_create_and_transition_session(self):
        self.client.force_authenticate(self.owner)
        created = self.client.post("/api/sessions/", {"title": "Radio repair", "description": "A sample"}, format="json")
        self.assertEqual(created.status_code, 201)
        session_id = created.data["id"]
        started = self.client.post(f"/api/sessions/{session_id}/start/", {}, format="json")
        self.assertEqual(started.status_code, 200)
        self.assertEqual(started.data["status"], CreatorSession.Status.LIVE)
        ended = self.client.post(f"/api/sessions/{session_id}/end/", {}, format="json")
        self.assertEqual(ended.status_code, 200)
        self.assertEqual(ended.data["status"], CreatorSession.Status.ENDED)

    def test_session_list_and_detail_are_scoped_to_owner(self):
        session = CreatorSession.objects.create(owner=self.owner, title="Private session")
        self.client.force_authenticate(self.other)
        listing = self.client.get("/api/sessions/")
        self.assertEqual(listing.data["count"], 0)
        detail = self.client.get(f"/api/sessions/{session.id}/")
        self.assertEqual(detail.status_code, 404)

    def test_title_is_required_and_trimmed(self):
        self.client.force_authenticate(self.owner)
        missing = self.client.post("/api/sessions/", {"title": " "}, format="json")
        self.assertEqual(missing.status_code, 400)
        created = self.client.post("/api/sessions/", {"title": "  Repair stream  "}, format="json")
        self.assertEqual(created.data["title"], "Repair stream")


class CreatorSessionWebsocketTests(TransactionTestCase):
    def setUp(self):
        users = get_user_model().objects
        self.owner = users.create_user(username="socket-owner", password="RiverGlass!308")
        self.other = users.create_user(username="socket-other", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=self.owner, title="Websocket session")
        self.owner_cookie = self.cookie_for(self.owner)
        self.other_cookie = self.cookie_for(self.other)
        self.origin = (b"origin", b"http://localhost:3000")

    @staticmethod
    def cookie_for(user):
        client = Client()
        client.force_login(user)
        return (b"cookie", f"sessionid={client.cookies['sessionid'].value}".encode())

    def communicator(self, cookie=None):
        headers = [self.origin]
        if cookie:
            headers.append(cookie)
        return WebsocketCommunicator(application, f"/ws/sessions/{self.session.id}/", headers=headers)

    async def test_owner_receives_only_session_scoped_events(self):
        communicator = self.communicator(self.owner_cookie)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await get_channel_layer().group_send(session_group_name(self.session.id), {"type": "signal_created", "payload": {"type": "signal.created", "signal": {"id": 4}}})
        event = await communicator.receive_json_from(timeout=2)
        self.assertEqual(event["type"], "signal.created")
        self.assertEqual(event["signal"]["id"], 4)
        await communicator.disconnect()

    async def test_other_creator_and_anonymous_viewer_are_rejected(self):
        other = self.communicator(self.other_cookie)
        accepted, code = await other.connect()
        self.assertFalse(accepted)
        self.assertEqual(code, 4404)
        anonymous = self.communicator()
        accepted, code = await anonymous.connect()
        self.assertFalse(accepted)
        self.assertEqual(code, 4401)

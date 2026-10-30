import uuid

from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase
from rest_framework.test import APIClient, APITestCase

from apps.feedback.models import ViewerFeedback
from apps.questions.models import QuestionCluster
from apps.responses.models import CreatorResponse
from apps.sessions.events import session_group_name
from apps.sessions.models import CreatorSession
from apps.signals.models import AudienceSignal
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


class CreatorWorkflowIntegrationTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="workflow-owner", password="RiverGlass!308")
        self.client.force_authenticate(self.owner)
        created = self.client.post("/api/sessions/", {"title": "Live radio restoration"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.session_id = created.data["id"]
        self.session_token = created.data["public_token"]
        started = self.client.post(f"/api/sessions/{self.session_id}/start/", {}, format="json")
        self.assertEqual(started.status_code, 200)
        self.viewer = APIClient()

    def signal_payload(self, question, region_key, participant_key=None):
        return {
            "session_token": self.session_token,
            "participant_key": str(participant_key or uuid.uuid4()),
            "idempotency_key": str(uuid.uuid4()),
            "region_x": "0.4250",
            "region_y": "0.6300",
            "region_key": region_key,
            "intent": "question",
            "question": question,
        }

    def test_live_creator_viewer_response_feedback_insights_workflow(self):
        first = self.viewer.post("/api/signals/", self.signal_payload("What does the amber tuning dial change?", "dial"), format="json")
        second = self.viewer.post("/api/signals/", self.signal_payload("How does the amber knob change the frequency?", "dial"), format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(AudienceSignal.objects.count(), 2)
        self.assertEqual(QuestionCluster.objects.count(), 1)

        groups = self.client.get(f"/api/sessions/{self.session_id}/questions/")
        self.assertEqual(groups.status_code, 200)
        self.assertEqual(groups.data[0]["signal_count"], 2)
        cluster_id = groups.data[0]["id"]

        drafted = self.client.post("/api/responses/", {"cluster_id": cluster_id, "text": "The dial changes the receiver’s tuning frequency."}, format="json")
        self.assertEqual(drafted.status_code, 201)
        published = self.client.post(f"/api/responses/{drafted.data['id']}/publish/", {}, format="json")
        self.assertEqual(published.status_code, 200)
        self.assertEqual(published.data["status"], CreatorResponse.Status.PUBLISHED)

        public = self.viewer.get(f"/api/feedback/public/sessions/{self.session_token}/responses/")
        self.assertEqual(public.status_code, 200)
        self.assertEqual(len(public.data["responses"]), 1)
        feedback_payload = {
            "session_token": self.session_token,
            "cluster_id": cluster_id,
            "participant_key": str(uuid.uuid4()),
            "idempotency_key": str(uuid.uuid4()),
            "helpful": True,
        }
        feedback = self.viewer.post("/api/feedback/", feedback_payload, format="json")
        self.assertEqual(feedback.status_code, 201)
        self.assertEqual(ViewerFeedback.objects.count(), 1)

        summary = self.client.get(f"/api/sessions/{self.session_id}/summary/")
        attention = self.client.get(f"/api/sessions/{self.session_id}/attention/")
        self.assertEqual(summary.data, {
            "session_id": self.session_id,
            "signal_count": 2,
            "question_groups": 1,
            "published_responses": 1,
            "feedback_count": 1,
            "helpful_feedback_count": 1,
        })
        self.assertEqual(attention.data["signal_count"], 2)
        self.assertEqual(attention.data["region_summary"], [{"region_key": "dial", "count": 2}])
        self.assertEqual(CreatorSession.objects.get(pk=self.session_id).status, CreatorSession.Status.LIVE)


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

    async def test_signal_api_publishes_event_to_connected_creator(self):
        self.session.status = CreatorSession.Status.LIVE
        await sync_to_async(self.session.save, thread_sensitive=True)(update_fields=["status"])
        communicator = self.communicator(self.owner_cookie)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        payload = {
            "session_token": str(self.session.public_token),
            "participant_key": str(uuid.uuid4()),
            "idempotency_key": str(uuid.uuid4()),
            "region_x": "0.2500",
            "region_y": "0.7500",
            "region_key": "dial",
            "intent": "curious",
            "question": "What is this dial for?",
        }
        response = await sync_to_async(APIClient().post, thread_sensitive=True)("/api/signals/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        event = await communicator.receive_json_from(timeout=2)
        self.assertEqual(event["type"], "signal.created")
        self.assertEqual(event["signal"]["question"], "What is this dial for?")
        await communicator.disconnect()

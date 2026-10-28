import uuid

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.questions.models import QuestionCluster
from apps.responses.models import CreatorResponse
from apps.sessions.models import CreatorSession


class ViewerFeedbackApiTests(APITestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user(username="feedback-owner", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=owner, title="Feedback session", status=CreatorSession.Status.LIVE)
        cluster = QuestionCluster.objects.create(session=self.session, label="How does it work?", match_key="work", region_key="dial")
        self.response = CreatorResponse.objects.create(cluster=cluster, creator=owner, text="It tunes the receiver.", status=CreatorResponse.Status.PUBLISHED)
        self.payload = {"session_token": str(self.session.public_token), "cluster_id": cluster.id, "participant_key": str(uuid.uuid4()), "idempotency_key": str(uuid.uuid4()), "helpful": True}

    def test_public_feedback_is_idempotent_and_aggregated(self):
        saved = self.client.post("/api/feedback/", self.payload, format="json")
        self.assertEqual(saved.status_code, 201)
        self.assertEqual(saved.data["feedback_count"], 1)
        replay = self.client.post("/api/feedback/", self.payload, format="json")
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.data["duplicate"])
        owner_client = self.client
        owner_client.force_authenticate(self.response.creator)
        aggregate = owner_client.get(f"/api/responses/{self.response.id}/feedback/")
        self.assertEqual(aggregate.data["helpful_count"], 1)

    def test_public_view_only_lists_published_responses(self):
        response = self.client.get(f"/api/feedback/public/sessions/{self.session.public_token}/responses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["responses"]), 1)
        self.response.status = CreatorResponse.Status.DRAFT
        self.response.save(update_fields=["status"])
        response = self.client.get(f"/api/feedback/public/sessions/{self.session.public_token}/responses/")
        self.assertEqual(response.data["responses"], [])

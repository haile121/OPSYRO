import uuid

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.questions.models import QuestionCluster
from apps.sessions.models import CreatorSession
from .models import AudienceSignal


class AudienceSignalApiTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="maker", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=self.owner, title="Radio repair", status=CreatorSession.Status.LIVE)
        self.payload = {
            "session_token": str(self.session.public_token),
            "participant_key": str(uuid.uuid4()),
            "idempotency_key": str(uuid.uuid4()),
            "region_x": "0.4250",
            "region_y": "0.6300",
            "region_key": "dial",
            "intent": "question",
            "question": "What does the amber dial change?",
        }

    def test_signal_is_stored_and_question_is_grouped(self):
        created = self.client.post("/api/signals/", self.payload, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(AudienceSignal.objects.count(), 1)
        duplicate = self.client.post("/api/signals/", self.payload, format="json")
        self.assertEqual(duplicate.status_code, 200)
        self.assertTrue(duplicate.data["duplicate"])
        self.assertEqual(AudienceSignal.objects.count(), 1)

    def test_similar_questions_at_same_region_share_a_cluster(self):
        self.client.post("/api/signals/", self.payload, format="json")
        second = {**self.payload, "participant_key": str(uuid.uuid4()), "idempotency_key": str(uuid.uuid4()), "question": "How does the tuning dial change the signal?"}
        response = self.client.post("/api/signals/", second, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(QuestionCluster.objects.count(), 1)
        self.assertEqual(AudienceSignal.objects.values("cluster_id").distinct().count(), 1)

    def test_coordinates_and_live_session_are_required(self):
        outside = {**self.payload, "region_x": "1.01"}
        invalid = self.client.post("/api/signals/", outside, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.session.status = CreatorSession.Status.DRAFT
        self.session.save(update_fields=["status"])
        unavailable = self.client.post("/api/signals/", self.payload, format="json")
        self.assertEqual(unavailable.status_code, 404)
        self.assertEqual(AudienceSignal.objects.count(), 0)

    def test_creator_queries_are_private_and_attention_is_aggregated(self):
        self.client.post("/api/signals/", self.payload, format="json")
        self.client.force_authenticate(self.owner)
        questions = self.client.get(f"/api/sessions/{self.session.id}/questions/")
        self.assertEqual(questions.status_code, 200)
        self.assertEqual(questions.data[0]["signal_count"], 1)
        self.assertEqual(len(questions.data[0]["example_questions"]), 1)
        attention = self.client.get(f"/api/sessions/{self.session.id}/attention/")
        self.assertEqual(attention.data["signal_count"], 1)
        self.assertEqual(attention.data["cells"][0]["count"], 1)
        self.assertNotIn("participant_key", str(questions.data))

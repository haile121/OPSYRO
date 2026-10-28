from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.questions.models import QuestionCluster
from apps.sessions.models import CreatorSession
from .models import CreatorResponse


class CreatorResponseApiTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="responder", password="RiverGlass!308")
        self.other = get_user_model().objects.create_user(username="stranger", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=self.owner, title="Live session", status=CreatorSession.Status.LIVE)
        self.cluster = QuestionCluster.objects.create(session=self.session, label="What does the dial change?", match_key="change dial", region_key="dial")

    def test_owner_can_draft_then_publish_and_cannot_edit_published(self):
        self.client.force_authenticate(self.owner)
        created = self.client.post("/api/responses/", {"cluster_id": self.cluster.id, "text": "The dial changes the tuning range."}, format="json")
        self.assertEqual(created.status_code, 201)
        response_id = created.data["id"]
        self.assertEqual(created.data["status"], CreatorResponse.Status.DRAFT)
        updated = self.client.patch(f"/api/responses/{response_id}/", {"text": "It adjusts the receiver's tuning range."}, format="json")
        self.assertEqual(updated.status_code, 200)
        published = self.client.post(f"/api/responses/{response_id}/publish/", {}, format="json")
        self.assertEqual(published.data["status"], CreatorResponse.Status.PUBLISHED)
        denied_edit = self.client.patch(f"/api/responses/{response_id}/", {"text": "Changed later."}, format="json")
        self.assertEqual(denied_edit.status_code, 400)

    def test_creator_cannot_respond_to_another_owners_question(self):
        self.client.force_authenticate(self.other)
        denied = self.client.post("/api/responses/", {"cluster_id": self.cluster.id, "text": "Not yours."}, format="json")
        self.assertEqual(denied.status_code, 400)

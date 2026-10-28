from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.experiments.models import Experiment
from apps.sessions.models import CreatorSession


class ExperimentApiTests(APITestCase):
    def setUp(self):
        users = get_user_model().objects
        self.owner = users.create_user(username="experiment-owner", password="RiverGlass!308")
        self.other = users.create_user(username="experiment-other", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=self.owner, title="Questions after demo")
        self.foreign_session = CreatorSession.objects.create(owner=self.other, title="Private session")
        self.client.force_authenticate(self.owner)

    def test_create_start_complete_and_record_outcome(self):
        created = self.client.post("/api/experiments/", {
            "name": "Add a pause for questions",
            "hypothesis": "A pause will reveal more questions about the demo.",
            "change": "Pause after the first segment.",
            "session_ids": [self.session.id],
        }, format="json")
        self.assertEqual(created.status_code, 201)
        experiment_id = created.data["id"]
        self.assertEqual(created.data["session_ids"], [self.session.id])
        started = self.client.post(f"/api/experiments/{experiment_id}/start/", {}, format="json")
        self.assertEqual(started.data["status"], Experiment.Status.ACTIVE)
        updated = self.client.patch(f"/api/experiments/{experiment_id}/", {"outcome": "The group asked two follow-up questions."}, format="json")
        self.assertEqual(updated.data["outcome"], "The group asked two follow-up questions.")
        completed = self.client.post(f"/api/experiments/{experiment_id}/complete/", {}, format="json")
        self.assertEqual(completed.data["status"], Experiment.Status.COMPLETE)

    def test_foreign_session_cannot_be_linked(self):
        response = self.client.post("/api/experiments/", {"name": "Invalid link", "session_ids": [self.foreign_session.id]}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_experiments_are_private_to_owner(self):
        experiment = Experiment.objects.create(owner=self.owner, name="Private learning")
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/experiments/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/experiments/{experiment.id}/").status_code, 404)

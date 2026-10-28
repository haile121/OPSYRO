from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class AccountFlowTests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_headers(self):
        self.client.get("/api/auth/csrf/")
        return {"HTTP_X_CSRFTOKEN": self.client.cookies["csrftoken"].value}

    def test_registration_requires_csrf_and_creates_account(self):
        payload = {"username": "curious", "email": "curious@example.com", "password": "RiverGlass!308"}
        denied = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(denied.status_code, 403)
        created = self.client.post("/api/auth/register/", payload, format="json", **self.csrf_headers())
        self.assertEqual(created.status_code, 201)
        self.assertNotIn("password", created.data)
        self.assertTrue(get_user_model().objects.filter(username="curious").exists())

    def test_login_and_logout_are_csrf_protected(self):
        user = get_user_model().objects.create_user(username="creator", email="creator@example.com", password="RiverGlass!308")
        denied = self.client.post("/api/auth/login/", {"username": user.username, "password": "RiverGlass!308"}, format="json")
        self.assertEqual(denied.status_code, 403)
        signed_in = self.client.post("/api/auth/login/", {"username": user.username, "password": "RiverGlass!308"}, format="json", **self.csrf_headers())
        self.assertEqual(signed_in.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").data["username"], "creator")
        signed_out = self.client.post("/api/auth/logout/", {}, format="json", **self.csrf_headers())
        self.assertEqual(signed_out.status_code, 204)

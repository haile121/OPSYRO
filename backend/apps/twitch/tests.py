import base64
import hashlib
import hmac
import json
import time
import uuid
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from cryptography.fernet import Fernet

from apps.sessions.models import CreatorSession
from .models import TwitchConnection


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def signed_token(secret, exp=None):
    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    claims = {"exp": exp or int(time.time()) + 60, "opaque_user_id": "U123", "channel_id": "98765", "role": "viewer"}
    payload = b64(json.dumps(claims).encode())
    content = f"{header}.{payload}".encode()
    key = base64.b64decode(secret)
    signature = b64(hmac.new(key, content, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


@override_settings(TWITCH_EXTENSION_SECRET="c2VjcmV0")
class TwitchExtensionApiTests(APITestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user(username="twitch-owner", password="RiverGlass!308")
        self.session = CreatorSession.objects.create(owner=owner, title="Live extension session", status="live", twitch_channel_id="98765")

    def test_signed_extension_token_resolves_only_live_channel_session(self):
        response = self.client.post("/api/twitch/extension/session/", {}, HTTP_X_TWITCH_EXTENSION_JWT=signed_token("c2VjcmV0"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["session_token"], str(self.session.public_token))

    def test_invalid_signature_is_rejected(self):
        response = self.client.post("/api/twitch/extension/session/", {}, HTTP_X_TWITCH_EXTENSION_JWT=signed_token("d3Jvbmc="))
        self.assertEqual(response.status_code, 403)

    def test_expired_token_is_rejected(self):
        response = self.client.post("/api/twitch/extension/session/", {}, HTTP_X_TWITCH_EXTENSION_JWT=signed_token("c2VjcmV0", int(time.time()) - 1))
        self.assertEqual(response.status_code, 403)


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


@override_settings(
    TWITCH_CLIENT_ID="test-client-id",
    TWITCH_CLIENT_SECRET="test-client-secret",
    TWITCH_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"),
    TWITCH_REDIRECT_URI="http://localhost:8000/api/v1/auth/twitch/callback",
    TWITCH_OAUTH_RETURN_URL="http://localhost:3000/workspace",
)
class TwitchOAuthApiTests(APITestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="oauth-owner", password="RiverGlass!308")
        self.other = get_user_model().objects.create_user(username="oauth-other", password="RiverGlass!308")
        self.client.force_login(self.owner)

    def begin_authorization(self):
        response = self.client.get("/api/v1/auth/twitch/authorize/")
        self.assertEqual(response.status_code, 302, response.content)
        target = urlparse(response["Location"])
        params = parse_qs(target.query)
        self.assertEqual(target.netloc, "id.twitch.tv")
        self.assertEqual(target.path, "/oauth2/authorize")
        self.assertEqual(params["response_type"], ["code"])
        self.assertEqual(params["redirect_uri"], ["http://localhost:8000/api/v1/auth/twitch/callback"])
        return params["state"][0]

    def test_authorization_requires_creator_login(self):
        self.client.logout()
        response = self.client.get("/api/v1/auth/twitch/authorize/")
        self.assertEqual(response.status_code, 401, response.content)

    def test_authorization_code_exchange_fetches_profile_and_encrypts_tokens(self):
        state = self.begin_authorization()
        twitch_id = str(uuid.uuid4().int)
        token_payload = {
            "access_token": "access-token-value",
            "refresh_token": "refresh-token-value",
            "expires_in": 14400,
            "scope": [],
            "token_type": "bearer",
        }
        profile_payload = {"data": [{
            "id": twitch_id,
            "login": "opsyro_creator",
            "display_name": "OPSYRO Creator",
            "profile_image_url": "https://static-cdn.jtvnw.net/profile.png",
        }]}
        self.assertFalse(TwitchConnection.objects.exists())
        with patch("apps.twitch.oauth_views.urlopen", side_effect=[FakeHTTPResponse(token_payload), FakeHTTPResponse(profile_payload)]) as request:
            response = self.client.get("/api/v1/auth/twitch/callback", {"code": "one-time-code", "state": state})

        self.assertEqual(response.status_code, 302, response.content)
        self.assertEqual(response["Location"], "http://localhost:3000/workspace?twitch=connected")
        self.assertEqual(request.call_count, 2)
        token_request = request.call_args_list[0].args[0]
        self.assertIn(b"grant_type=authorization_code", token_request.data)
        self.assertIn(b"redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Ftwitch%2Fcallback", token_request.data)
        profile_request = request.call_args_list[1].args[0]
        self.assertEqual(profile_request.full_url, "https://api.twitch.tv/helix/users")
        self.assertEqual(profile_request.get_header("Authorization"), "Bearer access-token-value")
        self.assertEqual(profile_request.get_header("Client-id"), "test-client-id")

        connection = TwitchConnection.objects.get(owner=self.owner)
        self.assertNotEqual(connection.encrypted_access_token, "access-token-value")
        self.assertNotEqual(connection.encrypted_refresh_token, "refresh-token-value")
        self.assertEqual(connection.get_access_token(), "access-token-value")
        self.assertEqual(connection.get_refresh_token(), "refresh-token-value")

        status = self.client.get("/api/v1/auth/twitch/status/")
        self.assertEqual(status.status_code, 200)
        status_payload = json.loads(status.content)
        self.assertEqual(status_payload["profile"]["id"], twitch_id)
        self.assertEqual(status_payload["profile"]["display_name"], "OPSYRO Creator")
        self.assertNotIn("access_token", str(status_payload))
        self.assertNotIn("refresh_token", str(status_payload))

    def test_denied_authorization_returns_to_workspace_without_exchange(self):
        state = self.begin_authorization()
        with patch("apps.twitch.oauth_views.urlopen") as request:
            response = self.client.get("/api/v1/auth/twitch/callback", {"error": "access_denied", "state": state})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://localhost:3000/workspace?twitch=denied")
        request.assert_not_called()
        self.assertFalse(TwitchConnection.objects.exists())

    def test_expired_authorization_code_exchange_failure_does_not_persist_connection(self):
        state = self.begin_authorization()
        expired_code_error = HTTPError(
            "https://id.twitch.tv/oauth2/token",
            400,
            "Bad Request",
            {},
            BytesIO(b'{"status":400,"message":"Invalid authorization code"}'),
        )
        with patch("apps.twitch.oauth_views.urlopen", side_effect=expired_code_error):
            response = self.client.get("/api/v1/auth/twitch/callback", {"code": "expired-code", "state": state})

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("expired-code", response.content.decode())
        self.assertFalse(TwitchConnection.objects.exists())

    def test_reconnect_updates_existing_connection_and_status_never_exposes_tokens(self):
        twitch_id = str(uuid.uuid4().int)
        first_profile = {"data": [{"id": twitch_id, "login": "first_login", "display_name": "First Name"}]}
        second_profile = {"data": [{"id": twitch_id, "login": "second_login", "display_name": "Second Name"}]}
        first_tokens = {"access_token": "first-access", "refresh_token": "first-refresh", "expires_in": 3600, "scope": []}
        second_tokens = {"access_token": "second-access", "refresh_token": "second-refresh", "expires_in": 7200, "scope": []}

        first_state = self.begin_authorization()
        with patch("apps.twitch.oauth_views.urlopen", side_effect=[FakeHTTPResponse(first_tokens), FakeHTTPResponse(first_profile)]):
            first = self.client.get("/api/v1/auth/twitch/callback", {"code": "first-code", "state": first_state})
        self.assertEqual(first.status_code, 302)
        original = TwitchConnection.objects.get(owner=self.owner)
        original_pk = original.pk

        second_state = self.begin_authorization()
        with patch("apps.twitch.oauth_views.urlopen", side_effect=[FakeHTTPResponse(second_tokens), FakeHTTPResponse(second_profile)]):
            second = self.client.get("/api/v1/auth/twitch/callback", {"code": "second-code", "state": second_state})
        self.assertEqual(second.status_code, 302)

        self.assertEqual(TwitchConnection.objects.filter(owner=self.owner).count(), 1)
        connection = TwitchConnection.objects.get(owner=self.owner)
        self.assertEqual(connection.pk, original_pk)
        self.assertEqual(connection.login, "second_login")
        self.assertEqual(connection.get_access_token(), "second-access")
        self.assertEqual(connection.get_refresh_token(), "second-refresh")

        status = self.client.get("/api/v1/auth/twitch/status/")
        self.assertEqual(status.status_code, 200)
        payload = status.content.decode()
        self.assertIn("second_login", payload)
        self.assertNotIn("second-access", payload)
        self.assertNotIn("second-refresh", payload)

    def test_connection_status_requires_login_and_reports_disconnected_state(self):
        self.assertEqual(self.client.get("/api/v1/auth/twitch/status/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/twitch/status/").json(), {"connected": False, "profile": None})

        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/auth/twitch/status/").status_code, 401)

    def test_invalid_and_expired_state_never_exchange_code(self):
        state = self.begin_authorization()
        with patch("apps.twitch.oauth_views.urlopen") as request:
            invalid = self.client.get("/api/v1/auth/twitch/callback", {"code": "unused", "state": "wrong"})
            self.assertEqual(invalid.status_code, 400)
            request.assert_not_called()

        self.client.session["twitch_oauth_state"] = {"value": state, "created_at": int(time.time()) - 601, "owner_id": self.owner.pk}
        self.client.session.save()
        expired = self.client.get("/api/v1/auth/twitch/callback", {"code": "unused", "state": state})
        self.assertEqual(expired.status_code, 400)
        request.assert_not_called()

    def test_callback_state_does_not_survive_signing_into_another_creator(self):
        state = self.begin_authorization()
        self.client.force_login(self.other)
        response = self.client.get("/api/v1/auth/twitch/callback", {"code": "unused", "state": state})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(TwitchConnection.objects.exists())

    def test_exchange_or_profile_failure_does_not_persist_connection(self):
        state = self.begin_authorization()
        with patch("apps.twitch.oauth_views.urlopen", side_effect=[FakeHTTPResponse({"access_token": "access", "refresh_token": "refresh", "expires_in": 3600}), FakeHTTPResponse({"data": []})]):
            response = self.client.get("/api/v1/auth/twitch/callback", {"code": "one-time-code", "state": state})
        self.assertEqual(response.status_code, 502)
        self.assertFalse(TwitchConnection.objects.exists())


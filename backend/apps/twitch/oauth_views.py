import json
import secrets
import time
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from .models import TwitchConnection
from .token_storage import encrypt_token


TWITCH_AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_USERS_URL = "https://api.twitch.tv/helix/users"
OAUTH_STATE_SESSION_KEY = "twitch_oauth_state"
OAUTH_STATE_MAX_AGE_SECONDS = 600


class TwitchOAuthError(Exception):
    pass


def _oauth_error(message, status=400):
    response = JsonResponse({"detail": message}, status=status)
    response["Cache-Control"] = "no-store"
    return response


def _frontend_redirect(result):
    parts = urlsplit(settings.TWITCH_OAUTH_RETURN_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["twitch"] = result
    return HttpResponseRedirect(urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), "")))


def _read_json(url, *, data=None, headers=None):
    request = Request(
        url,
        data=data,
        headers=headers or {},
        method="POST" if data is not None else "GET",
    )
    try:
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        raise TwitchOAuthError from error
    if not isinstance(result, dict):
        raise TwitchOAuthError
    return result


def _exchange_code(code):
    form = urlencode({
        "client_id": settings.TWITCH_CLIENT_ID,
        "client_secret": settings.TWITCH_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.TWITCH_REDIRECT_URI,
    }).encode("ascii")
    token_data = _read_json(
        TWITCH_TOKEN_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    try:
        expires_in = int(token_data.get("expires_in", 0))
    except (TypeError, ValueError):
        expires_in = 0
    if not access_token or not refresh_token or expires_in <= 0:
        raise TwitchOAuthError
    return token_data, access_token, refresh_token, expires_in


def _get_authenticated_twitch_user(access_token):
    result = _read_json(
        TWITCH_USERS_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": settings.TWITCH_CLIENT_ID,
        },
    )
    users = result.get("data")
    if not isinstance(users, list) or not users or not isinstance(users[0], dict):
        raise TwitchOAuthError
    profile = users[0]
    if not profile.get("id") or not profile.get("login") or not profile.get("display_name"):
        raise TwitchOAuthError
    return profile


@method_decorator(never_cache, name="dispatch")
class TwitchOAuthAuthorizeView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return _oauth_error("Sign in to OPSYRO before connecting Twitch.", status=401)
        if not settings.TWITCH_CLIENT_ID or not settings.TWITCH_CLIENT_SECRET:
            return _oauth_error("Twitch OAuth is not configured.", status=503)
        if not settings.TWITCH_TOKEN_ENCRYPTION_KEY:
            return _oauth_error("Twitch token encryption is not configured.", status=503)

        state = secrets.token_urlsafe(32)
        request.session[OAUTH_STATE_SESSION_KEY] = {
            "value": state,
            "created_at": int(time.time()),
            "owner_id": request.user.pk,
        }
        query = urlencode({
            "client_id": settings.TWITCH_CLIENT_ID,
            "redirect_uri": settings.TWITCH_REDIRECT_URI,
            "response_type": "code",
            "scope": "",
            "state": state,
        })
        response = HttpResponseRedirect(f"{TWITCH_AUTHORIZE_URL}?{query}")
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(never_cache, name="dispatch")
class TwitchOAuthCallbackView(View):
    def get(self, request):
        # State is one-use and tied to the OPSYRO creator who initiated the flow.
        expected_state = request.session.pop(OAUTH_STATE_SESSION_KEY, None)
        supplied_state = request.GET.get("state", "")
        try:
            state_age = int(time.time()) - int(expected_state.get("created_at", 0))
        except (AttributeError, TypeError, ValueError):
            state_age = OAUTH_STATE_MAX_AGE_SECONDS + 1
        valid_state = (
            isinstance(expected_state, dict)
            and bool(supplied_state)
            and secrets.compare_digest(str(expected_state.get("value", "")), supplied_state)
            and 0 <= state_age <= OAUTH_STATE_MAX_AGE_SECONDS
        )
        if not valid_state:
            return _oauth_error("Twitch authorization state is missing, expired, or invalid.")
        if not request.user.is_authenticated or str(request.user.pk) != str(expected_state.get("owner_id")):
            return _oauth_error("Sign in to the same OPSYRO account to finish connecting Twitch.", status=401)

        if request.GET.get("error"):
            return _frontend_redirect("denied")
        code = request.GET.get("code", "")
        if not code:
            return _oauth_error("Twitch did not return an authorization code.")
        if not settings.TWITCH_CLIENT_ID or not settings.TWITCH_CLIENT_SECRET:
            return _oauth_error("Twitch OAuth is not configured.", status=503)

        try:
            token_data, access_token, refresh_token, expires_in = _exchange_code(code)
            profile = _get_authenticated_twitch_user(access_token)
            encrypted_access_token = encrypt_token(access_token)
            encrypted_refresh_token = encrypt_token(refresh_token)
        except ImproperlyConfigured:
            return _oauth_error("Twitch token encryption is not configured correctly.", status=503)
        except TwitchOAuthError:
            return _oauth_error("Twitch authorization could not be completed.", status=502)

        if TwitchConnection.objects.filter(twitch_user_id=str(profile["id"])).exclude(owner=request.user).exists():
            return _oauth_error("This Twitch account is already connected to another OPSYRO creator.", status=409)

        try:
            with transaction.atomic():
                scopes = token_data.get("scope", [])
                connection_values = {
                    "twitch_user_id": str(profile["id"]),
                    "login": str(profile["login"]),
                    "display_name": str(profile["display_name"]),
                    "profile_image_url": str(profile.get("profile_image_url", "")),
                    "encrypted_access_token": encrypted_access_token,
                    "encrypted_refresh_token": encrypted_refresh_token,
                    "scopes": scopes if isinstance(scopes, list) else [],
                    "token_expires_at": timezone.now() + timedelta(seconds=expires_in),
                }
                connection, _ = TwitchConnection.objects.get_or_create(
                    owner=request.user,
                    defaults=connection_values,
                )
                for field, value in connection_values.items():
                    setattr(connection, field, value)
                connection.save()
        except IntegrityError:
            conflict = TwitchConnection.objects.filter(twitch_user_id=str(profile["id"])).exclude(owner=request.user).exists()
            if conflict:
                return _oauth_error("This Twitch account is already connected to another OPSYRO creator.", status=409)
            return _oauth_error("Twitch connection could not be saved.", status=500)

        request.session.cycle_key()
        request.session.pop(OAUTH_STATE_SESSION_KEY, None)
        return _frontend_redirect("connected")


@method_decorator(never_cache, name="dispatch")
class TwitchConnectionStatusView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return _oauth_error("Sign in to OPSYRO to view connected accounts.", status=401)
        connection = TwitchConnection.objects.filter(owner=request.user).first()
        if connection is None:
            payload = {"connected": False, "profile": None}
        else:
            payload = {
                "connected": True,
                "profile": {
                    "id": connection.twitch_user_id,
                    "login": connection.login,
                    "display_name": connection.display_name,
                    "profile_image_url": connection.profile_image_url,
                },
            }
        response = JsonResponse(payload)
        response["Cache-Control"] = "no-store"
        return response

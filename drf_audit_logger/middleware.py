"""
AuditLogMiddleware for drf-audit-logger.

Authenticates the request using DRF's configured authenticators,
sets `request.user` for downstream middleware, and captures IP / User-Agent.

Important:
    This middleware MUST NOT read `request.body` or `request.POST`.
    Reading them consumes the request stream and breaks:
      - Django admin form submissions (CSRF / POST data)
      - Any downstream view that expects the body intact
    In particular, `SessionAuthentication.enforce_csrf()` reads
    `request.POST`, so it must never be invoked here.
"""
import logging

from django.utils.module_loading import import_string
from rest_framework.authentication import SessionAuthentication
from rest_framework.settings import api_settings as drf_settings

from . import _local

logger = logging.getLogger(__name__)


class AuditLogMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self._authenticators = self._load_authenticators()

    @staticmethod
    def _load_authenticators():
        """
        Load DRF authenticators EXCEPT SessionAuthentication.

        Why exclude SessionAuthentication?
        ----------------------------------
        Its `authenticate()` calls `enforce_csrf()`, which reads
        `request.POST`. On a Django HttpRequest, accessing `.POST` triggers
        `_load_post_and_files()` → FormParser.parse(stream) → `stream.read()`,
        which sets `request._read_started = True` and permanently marks the
        body as consumed. Every later access to `request.POST` (including
        Django's CsrfViewMiddleware) then returns empty, and CSRF checks fail.

        Session-authenticated users are instead resolved from
        `request.user` (set by Django's AuthenticationMiddleware).
        """
        instances = []
        for entry in getattr(drf_settings, "DEFAULT_AUTHENTICATION_CLASSES", ()):
            try:
                cls = import_string(entry) if isinstance(entry, str) else entry

                if isinstance(cls, type) and issubclass(cls, SessionAuthentication):
                    continue

                instances.append(cls())
            except Exception as exc:
                logger.warning("Could not load authenticator %r: %s", entry, exc)
        return tuple(instances)

    def __call__(self, request):
        _local.set_current_request(request)
        self._authenticate(request)
        self._capture_ip(request)
        self._capture_user_agent(request)

        try:
            response = self.get_response(request)
        finally:
            _local.clear()

        return response

    def _authenticate(self, request):
        user = None
        auth_method = None
        auth_token = None

        # 1) Session-based user — already set by AuthenticationMiddleware.
        #    No body access, no CSRF enforcement, no side effects.
        dj_user = getattr(request, "user", None)
        if dj_user is not None and dj_user.is_authenticated:
            user = dj_user
            auth_method = "DjangoSessionAuthentication"

        # 2) Otherwise try the non-session authenticators (JWT, Token, ...).
        #    These only read headers, never the body.
        if user is None:
            for authenticator in self._authenticators:
                try:
                    result = authenticator.authenticate(request)
                except Exception as exc:
                    logger.debug(
                        "Auth attempt failed (%s): %s",
                        type(authenticator).__name__, exc,
                    )
                    continue

                if result is None:
                    continue

                user, auth_token = result
                auth_method = type(authenticator).__name__
                break

        if user is not None:
            request.user = user

        request.auth_method = auth_method
        request.auth_token = auth_token
        _local.set_current_user(user)

    def _capture_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
        _local.set_current_ip(ip)

    def _capture_user_agent(self, request):
        _local.set_current_user_agent(request.META.get("HTTP_USER_AGENT", "")[:1000])
"""
AuditLogMiddleware for drf-audit-logger.

- Uses DRF's DEFAULT_AUTHENTICATION_CLASSES to authenticate the request.
- Sets `request.user` so downstream middleware can read it.
- Detects and exposes the authentication method used.
- Never breaks the request pipeline on auth failure.
"""
import logging

from django.utils.module_loading import import_string
from rest_framework.request import Request as DRFRequest
from rest_framework.settings import api_settings as drf_settings

from . import _local

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """
    Middleware that:
    1. Authenticates the request using DRF's configured authenticators.
    2. Sets `request.user` for downstream middleware.
    3. Captures IP address and User-Agent in thread-local storage.
    4. Exposes `request.auth_method` for logging purposes.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._authenticators = self._load_authenticators()

    @staticmethod
    def _load_authenticators():
        """
        Load DRF authenticators from DEFAULT_AUTHENTICATION_CLASSES.

        Note: DRF's `DEFAULT_AUTHENTICATION_CLASSES` returns classes,
        not strings, so we must check the type before calling import_string.
        """
        instances = []
        for entry in getattr(drf_settings, "DEFAULT_AUTHENTICATION_CLASSES", ()):
            try:
                cls = import_string(entry) if isinstance(entry, str) else entry
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

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------
    def _authenticate(self, request):
        """
        Authenticate the request using DRF's authenticators.
        Falls back to Django's session-based auth if needed.
        """
        user = None
        auth_method = None
        auth_token = None

        # 1) Try DRF's configured authenticators (JWT, Token, etc.)
        if self._authenticators:
            try:
                drf_request = DRFRequest(
                    request,
                    authenticators=self._authenticators,
                )
                drf_user = drf_request.user
                if drf_user and drf_user.is_authenticated:
                    user = drf_user
                    auth_token = getattr(drf_request, "auth", None)
                    authenticator = getattr(drf_request, "_authenticator", None)
                    auth_method = (
                        type(authenticator).__name__ if authenticator else "DRF"
                    )
            except Exception as exc:
                logger.debug("DRF auth attempt failed: %s", exc)

        # 2) Fallback to Django's session-based authentication
        if user is None:
            dj_user = getattr(request, "user", None)
            if dj_user is not None and dj_user.is_authenticated:
                user = dj_user
                auth_method = "DjangoSessionAuthentication"

        # Set the authenticated user on the Django request
        # so downstream middleware (e.g. UserMMiddleware) can read it.
        if user is not None:
            request.user = user

        # Expose auth metadata on the request
        request.auth_method = auth_method
        request.auth_token = auth_token

        # Store in thread-local for signal handlers
        _local.set_current_user(user)

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------
    def _capture_ip(self, request):
        """Extract the client IP address from the request."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
        _local.set_current_ip(ip)

    def _capture_user_agent(self, request):
        """Extract the user agent from the request."""
        _local.set_current_user_agent(
            request.META.get("HTTP_USER_AGENT", "")[:1000]
        )
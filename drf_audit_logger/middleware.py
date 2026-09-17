"""
AuditLogMiddleware for drf-audit-logger.

Authenticates the request using DRF's configured authenticators,
sets `request.user` for downstream middleware, and captures IP / User-Agent.
"""
import logging

from django.utils.module_loading import import_string
from rest_framework.request import Request as DRFRequest
from rest_framework.settings import api_settings as drf_settings

from . import _local

logger = logging.getLogger(__name__)


class AuditLogMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self._authenticators = self._load_authenticators()

    @staticmethod
    def _load_authenticators():
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

    def _authenticate(self, request):
        user = None
        auth_method = None
        auth_token = None

        if self._authenticators:
            try:
                drf_request = DRFRequest(request, authenticators=self._authenticators)
                drf_user = drf_request.user
                if drf_user and drf_user.is_authenticated:
                    user = drf_user
                    auth_token = getattr(drf_request, "auth", None)
                    authenticator = getattr(drf_request, "_authenticator", None)
                    auth_method = type(authenticator).__name__ if authenticator else "DRF"
            except Exception as exc:
                logger.debug("DRF auth attempt failed: %s", exc)

        if user is None:
            dj_user = getattr(request, "user", None)
            if dj_user is not None and dj_user.is_authenticated:
                user = dj_user
                auth_method = "DjangoSessionAuthentication"

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
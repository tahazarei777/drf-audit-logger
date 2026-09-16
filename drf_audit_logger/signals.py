"""
Django signals for drf-audit-logger.

Connects to:
- post_save: for create and update events
- post_delete: for delete events
- user_logged_in, user_logged_out, user_login_failed: for auth events
"""
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import post_save, post_delete

from ._local import (
    get_current_user,
    get_current_ip,
    get_current_user_agent,
)
from .conf import (
    is_model_excluded,
    is_model_logging_enabled,
    is_auth_logging_enabled,
)
from .services import AuditLogService


# ============================================================
# MODEL SIGNALS
# ============================================================

def handle_post_save(sender, instance, created, raw, **kwargs):
    """
    Handle post_save signal for all models.

    - If created=True → log a CREATE event.
    - If created=False → log an UPDATE event (only if there are changes).

    Skips:
    - Fixture loading (raw=True)
    - Excluded models
    - Models without a primary key
    """
    if raw:
        return
    if not is_model_logging_enabled():
        return

    if is_model_excluded(sender):
        return

    user = get_current_user()
    ip_address = get_current_ip()
    user_agent = get_current_user_agent()

    if created:
        AuditLogService.log_create(
            instance=instance,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    else:
        AuditLogService.log_update(
            instance=instance,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )


def handle_post_delete(sender, instance, **kwargs):
    """
    Handle post_delete signal for all models.

    Skips:
    - Excluded models
    """
    if not is_model_logging_enabled():
        return

    if is_model_excluded(sender):
        return

    user = get_current_user()
    ip_address = get_current_ip()
    user_agent = get_current_user_agent()

    AuditLogService.log_delete(
        instance=instance,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ============================================================
# AUTH SIGNALS
# ============================================================

def handle_user_logged_in(sender, request, user, **kwargs):
    """Handle user_logged_in signal."""
    if not is_auth_logging_enabled():
        return

    ip_address = _get_ip_from_request(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''

    AuditLogService.log_login(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def handle_user_logged_out(sender, request, user, **kwargs):
    """Handle user_logged_out signal."""
    if not is_auth_logging_enabled():
        return

    if user is None:
        return

    ip_address = _get_ip_from_request(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''

    AuditLogService.log_logout(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def handle_user_login_failed(sender, credentials, request, **kwargs):
    """Handle user_login_failed signal."""
    if not is_auth_logging_enabled():
        return

    username = credentials.get('username') or credentials.get('email') or ''
    ip_address = _get_ip_from_request(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''

    AuditLogService.log_login_failed(
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def _get_ip_from_request(request):
    """Extract the client IP from a request."""
    if not request:
        return None

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ============================================================
# REGISTRATION
# ============================================================

def register_signals():
    """
    Register all signals.

    Called from AppConfig.ready().
    """

    post_save.connect(
        handle_post_save,
        dispatch_uid='drf_audit_logger_post_save',
    )
    post_delete.connect(
        handle_post_delete,
        dispatch_uid='drf_audit_logger_post_delete',
    )

    user_logged_in.connect(
        handle_user_logged_in,
        dispatch_uid='drf_audit_logger_user_logged_in',
    )
    user_logged_out.connect(
        handle_user_logged_out,
        dispatch_uid='drf_audit_logger_user_logged_out',
    )
    user_login_failed.connect(
        handle_user_login_failed,
        dispatch_uid='drf_audit_logger_user_login_failed',
    )

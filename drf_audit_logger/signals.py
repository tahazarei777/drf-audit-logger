"""Django signals for drf-audit-logger."""
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db import models as dj_models
from django.db.models.signals import post_save, post_delete, pre_save

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
# SNAPSHOT STORAGE
# ============================================================
# We store the "before" state of each instance in memory before save,
# so that post_save can compare old vs new values.

_OLD_VALUES = {}


def _make_key(instance):
    return f"{instance.__class__.__name__}:{instance.pk}"


# ============================================================
# PRE_SAVE: capture old values before they're overwritten
# ============================================================

def handle_pre_save(sender, instance, raw, **kwargs):
    """Capture current DB values before the save happens."""
    if raw:
        return
    if not is_model_logging_enabled():
        return
    if is_model_excluded(sender):
        return

    # If it's a new object (no pk yet), there's nothing to snapshot
    if not instance.pk:
        return

    # Fetch the current DB state
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    # Snapshot all concrete field values
    snapshot = {}
    for field in old_instance._meta.get_fields():
        if not isinstance(field, dj_models.Field):
            continue
        try:
            snapshot[field.name] = getattr(old_instance, field.name, None)
        except Exception:
            continue

    _OLD_VALUES[_make_key(instance)] = snapshot


# ============================================================
# POST_SAVE
# ============================================================

def handle_post_save(sender, instance, created, raw, **kwargs):
    if raw:
        return
    if not is_model_logging_enabled():
        return
    if is_model_excluded(sender):
        return

    user = get_current_user()
    ip = get_current_ip()
    ua = get_current_user_agent()

    if created:
        AuditLogService.log_create(
            instance=instance, user=user, ip_address=ip, user_agent=ua,
        )
    else:
        # Retrieve the old values we captured in pre_save
        key = _make_key(instance)
        old_values = _OLD_VALUES.pop(key, None)

        AuditLogService.log_update(
            instance=instance,
            user=user,
            ip_address=ip,
            user_agent=ua,
            old_values=old_values,
        )


def handle_post_delete(sender, instance, **kwargs):
    if not is_model_logging_enabled():
        return
    if is_model_excluded(sender):
        return

    user = get_current_user()
    ip = get_current_ip()
    ua = get_current_user_agent()

    AuditLogService.log_delete(
        instance=instance, user=user, ip_address=ip, user_agent=ua,
    )


# ============================================================
# AUTH SIGNALS
# ============================================================

def handle_user_logged_in(sender, request, user, **kwargs):
    if not is_auth_logging_enabled():
        return
    ip = _get_ip_from_request(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''
    AuditLogService.log_login(user=user, ip_address=ip, user_agent=ua)


def handle_user_logged_out(sender, request, user, **kwargs):
    if not is_auth_logging_enabled():
        return
    if user is None:
        return
    ip = _get_ip_from_request(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''
    AuditLogService.log_logout(user=user, ip_address=ip, user_agent=ua)


def handle_user_login_failed(sender, credentials, request, **kwargs):
    if not is_auth_logging_enabled():
        return
    username = credentials.get('username') or credentials.get('email') or ''
    ip = _get_ip_from_request(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:1000] if request else ''
    AuditLogService.log_login_failed(username=username, ip_address=ip, user_agent=ua)


def _get_ip_from_request(request):
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ============================================================
# REGISTRATION
# ============================================================

def register_signals():
    pre_save.connect(handle_pre_save, dispatch_uid='drf_audit_logger_pre_save')
    post_save.connect(handle_post_save, dispatch_uid='drf_audit_logger_post_save')
    post_delete.connect(handle_post_delete, dispatch_uid='drf_audit_logger_post_delete')
    user_logged_in.connect(handle_user_logged_in, dispatch_uid='drf_audit_logger_user_logged_in')
    user_logged_out.connect(handle_user_logged_out, dispatch_uid='drf_audit_logger_user_logged_out')
    user_login_failed.connect(handle_user_login_failed, dispatch_uid='drf_audit_logger_user_login_failed')
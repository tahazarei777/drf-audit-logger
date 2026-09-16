from django.db import models

from .conf import (
    get_sensitive_fields,
    get_max_field_length,
    is_model_excluded,
    is_model_logging_enabled,
)

# ============================================================
# HELPERS
# ============================================================

def get_field_verbose_name(model, field_name):
    """Return the translated verbose_name of a model field."""
    try:
        field = model._meta.get_field(field_name)
        return field.verbose_name
    except Exception:
        return field_name.replace('_', ' ').title()


def is_sensitive_field(field_name):
    """Check if a field is in the sensitive list."""
    sensitive = get_sensitive_fields()
    return field_name.lower() in [f.lower() for f in sensitive]


def mask_value(value):
    """Replace sensitive value with a mask."""
    return '***MASKED***'


def serialize_value(value):
    """Convert a value to a JSON-serializable format."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, str):
            max_len = get_max_field_length()
            if len(value) > max_len:
                return value[:max_len] + '…'
        return value
    if isinstance(value, (list, tuple)):
        return [serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): serialize_value(v) for k, v in value.items()}
    return str(value)


# ============================================================
# CHANGE DETECTION
# ============================================================

def detect_changes(instance):
    """
    Compare current instance values with the database values
    and return a dictionary of changes.

    Returns:
        {
            "field_name": {
                "old": <old value>,
                "new": <new value>,
                "field_verbose": <translated verbose name>,
            },
            ...
        }
        or None if no changes.
    """
    if not instance.pk:
        return None

    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return None

    changes = {}

    for field in instance._meta.get_fields():
        if not isinstance(field, models.Field):
            continue
        if field.primary_key:
            continue
        if field.name in ('created_at', 'updated_at'):
            continue

        try:
            old_value = getattr(old_instance, field.name, None)
            new_value = getattr(instance, field.name, None)
        except Exception:
            continue

        if old_value == new_value:
            continue

        if is_sensitive_field(field.name):
            changes[field.name] = {
                'old': mask_value(old_value),
                'new': mask_value(new_value),
                'field_verbose': get_field_verbose_name(instance.__class__, field.name),
            }
        else:
            changes[field.name] = {
                'old': serialize_value(old_value),
                'new': serialize_value(new_value),
                'field_verbose': get_field_verbose_name(instance.__class__, field.name),
            }

    return changes if changes else None


def build_create_changes(instance):
    changes = {}

    for field in instance._meta.get_fields():
        if not isinstance(field, models.Field):
            continue
        if field.primary_key:
            continue
        if field.name in ('created_at', 'updated_at'):
            continue

        try:
            value = getattr(instance, field.name, None)
        except Exception:
            continue

        if value is None:
            continue

        if is_sensitive_field(field.name):
            changes[field.name] = mask_value(value)
        else:
            changes[field.name] = serialize_value(value)

    return changes if changes else None


def build_delete_changes(instance):
    return build_create_changes(instance)


class AuditLogService:

    @staticmethod
    def create_log(
            action,
            user=None,
            instance=None,
            changes=None,
            metadata=None,
            ip_address=None,
            user_agent=None,
    ):
        from .models import AuditLog
        if instance is not None and is_model_excluded(instance.__class__):
            return None
        model_name = ''
        object_id = ''
        object_repr = ''

        if instance is not None:
            model_name = instance.__class__.__name__
            object_id = str(instance.pk) if instance.pk else ''
            try:
                object_repr = str(instance)[:255]
            except Exception:
                object_repr = ''
        return AuditLog.objects.create(
            action=action,
            user=user,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent or '',
        )

    @staticmethod
    def log_create(instance, user=None, ip_address=None, user_agent=None):
        from .models import AuditLog

        if not is_model_logging_enabled():
            return None

        changes = build_create_changes(instance)

        return AuditLogService.create_log(
            action=AuditLog.ACTION_CREATE,
            user=user,
            instance=instance,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_update(instance, user=None, ip_address=None, user_agent=None):
        from .models import AuditLog

        if not is_model_logging_enabled():
            return None

        changes = detect_changes(instance)
        if not changes:
            return None

        return AuditLogService.create_log(
            action=AuditLog.ACTION_UPDATE,
            user=user,
            instance=instance,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_delete(instance, user=None, ip_address=None, user_agent=None):
        from .models import AuditLog

        if not is_model_logging_enabled():
            return None

        changes = build_delete_changes(instance)

        return AuditLogService.create_log(
            action=AuditLog.ACTION_DELETE,
            user=user,
            instance=instance,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_login(user, ip_address=None, user_agent=None):
        from .models import AuditLog

        return AuditLogService.create_log(
            action=AuditLog.ACTION_LOGIN,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_logout(user, ip_address=None, user_agent=None):
        from .models import AuditLog

        return AuditLogService.create_log(
            action=AuditLog.ACTION_LOGOUT,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_login_failed(username=None, ip_address=None, user_agent=None):
        from .models import AuditLog

        metadata = {}
        if username:
            metadata['username'] = username

        return AuditLogService.create_log(
            action=AuditLog.ACTION_LOGIN_FAILED,
            user=None,
            metadata=metadata or None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_custom(user, message_id, params=None, ip_address=None, user_agent=None):
        from .models import AuditLog

        return AuditLogService.create_log(
            action=AuditLog.ACTION_CUSTOM,
            user=user,
            metadata={
                'message_id': message_id,
                'params': params or {},
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )


def log(user, action='custom', message_id=None, params=None, **kwargs):
    if action == 'custom':
        return AuditLogService.log_custom(
            user=user,
            message_id=message_id,
            params=params,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
        )

    return AuditLogService.create_log(
        action=action,
        user=user,
        metadata={'message_id': message_id, 'params': params} if message_id else None,
        **kwargs,
    )

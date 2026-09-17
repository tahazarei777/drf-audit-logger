"""Message renderer for drf-audit-logger.

All messages are rendered using gettext, so they automatically adapt
to the active language at display time.

Field verbose names are looked up dynamically from the model,
so translations of fields work at render time (not at storage time).
"""
from django.apps import apps
from django.utils.translation import gettext as _


# ============================================================
# HELPERS
# ============================================================

def get_user_display(log):
    return log.user_display


def find_model_class(model_name):
    """Find a model class by its name across all apps."""
    if not model_name:
        return None
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            if model.__name__ == model_name:
                return model
    return None


def get_model_verbose_name(log):
    """Return the translated verbose_name of the model (dynamic)."""
    model = find_model_class(log.model_name)
    if model is not None:
        return model._meta.verbose_name
    return log.model_name or _('object')


def get_field_verbose_name(log, field_name):
    """
    Look up the field's verbose_name from the model at render time.
    This makes field names translatable and dynamic.
    """
    model = find_model_class(log.model_name)
    if model is not None:
        try:
            field = model._meta.get_field(field_name)
            return field.verbose_name
        except Exception:
            pass
    return field_name.replace('_', ' ').title()


def format_value(value):
    if value is None:
        return _('empty')
    if value is True:
        return _('Yes')
    if value is False:
        return _('No')
    if isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value) or _('empty')
    if isinstance(value, dict):
        return ', '.join(f"{k}: {v}" for k, v in value.items()) or _('empty')

    text = str(value)
    if len(text) > 100:
        return text[:100] + '…'
    return text


# ============================================================
# RENDERERS
# ============================================================

def render_login(log):
    return _('User %(user)s logged in') % {'user': get_user_display(log)}


def render_logout(log):
    return _('User %(user)s logged out') % {'user': get_user_display(log)}


def render_login_failed(log):
    if log.ip_address:
        return _('Failed login attempt from IP %(ip)s') % {'ip': log.ip_address}
    return _('Failed login attempt')


def render_create(log):
    return _('User %(user)s created %(model)s "%(name)s"') % {
        'user': get_user_display(log),
        'model': get_model_verbose_name(log),
        'name': log.object_repr or f"#{log.object_id}",
    }


def render_delete(log):
    return _('User %(user)s deleted %(model)s "%(name)s"') % {
        'user': get_user_display(log),
        'model': get_model_verbose_name(log),
        'name': log.object_repr or f"#{log.object_id}",
    }


def render_update(log):
    if not log.changes:
        return _('User %(user)s updated %(model)s "%(name)s"') % {
            'user': get_user_display(log),
            'model': get_model_verbose_name(log),
            'name': log.object_repr or f"#{log.object_id}",
        }

    changes = log.changes

    # Single field
    if len(changes) == 1:
        field_name, change_data = next(iter(changes.items()))
        if isinstance(change_data, dict) and 'old' in change_data and 'new' in change_data:
            return _(
                'User %(user)s changed "%(field)s" of %(model)s "%(name)s" '
                'from "%(old)s" to "%(new)s"'
            ) % {
                'user': get_user_display(log),
                'field': get_field_verbose_name(log, field_name),  # dynamic
                'model': get_model_verbose_name(log),
                'name': log.object_repr or f"#{log.object_id}",
                'old': format_value(change_data.get('old')),
                'new': format_value(change_data.get('new')),
            }

    # Multiple fields
    return _('User %(user)s updated %(model)s "%(name)s" (%(count)d changes)') % {
        'user': get_user_display(log),
        'model': get_model_verbose_name(log),
        'name': log.object_repr or f"#{log.object_id}",
        'count': len(changes),
    }


def render_custom(log):
    metadata = log.metadata or {}
    message_id = metadata.get('message_id')
    params = metadata.get('params', {})

    if message_id:
        try:
            return _(message_id) % params
        except (KeyError, TypeError):
            return str(message_id)

    return _('Custom event by %(user)s') % {'user': get_user_display(log)}


# ============================================================
# MAIN
# ============================================================

ACTION_RENDERERS = {
    'login': render_login,
    'logout': render_logout,
    'login_failed': render_login_failed,
    'create': render_create,
    'update': render_update,
    'delete': render_delete,
    'custom': render_custom,
}


def render_audit_message(log):
    renderer = ACTION_RENDERERS.get(log.action)
    if renderer is None:
        return f"{log.action} - {log.object_repr}"
    try:
        return renderer(log)
    except Exception:
        return f"{log.action} - {log.object_repr}"
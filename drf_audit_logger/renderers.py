"""Message renderer for drf-audit-logger."""
from django.apps import apps
from django.utils.translation import gettext as _


# ============================================================
# HELPERS
# ============================================================

def get_user_display(log):
    """Human-readable name for the user."""
    return log.user_display


def get_model_verbose_name(log):
    """
    Return the translated verbose_name of the model.

    Tries to find the actual model class by name and use its
    verbose_name. Falls back to the raw model_name string.
    """
    if not log.model_name:
        return _('object')

    # جستجو در همه اپلیکیشن‌ها برای پیدا کردن مدل
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            if model.__name__ == log.model_name:
                # verbose_name با gettext_lazy تعریف شده، پس خودکار ترجمه می‌شود
                return model._meta.verbose_name

    # اگر مدل پیدا نشد، از خود رشته استفاده کن
    return log.model_name


def format_value(value):
    """Format a value for display in a message."""
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

    # تغییر تک‌فیلد
    if len(changes) == 1:
        field_name, change_data = next(iter(changes.items()))
        if isinstance(change_data, dict) and 'old' in change_data and 'new' in change_data:
            return _(
                'User %(user)s changed "%(field)s" of %(model)s "%(name)s" '
                'from "%(old)s" to "%(new)s"'
            ) % {
                'user': get_user_display(log),
                'field': change_data.get('field_verbose', field_name),
                'model': get_model_verbose_name(log),
                'name': log.object_repr or f"#{log.object_id}",
                'old': format_value(change_data.get('old')),
                'new': format_value(change_data.get('new')),
            }

    # چند فیلد
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
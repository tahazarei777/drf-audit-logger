"""Configuration reader for drf-audit-logger."""
from django.conf import settings


DEFAULTS = {
    'EXCLUDE_MODEL_LOGGING': [
        'admin.LogEntry',
        'sessions.Session',
        'contenttypes.ContentType',
        'drf_audit_logger.AuditLog',
        'authtoken.Token',
        'token_blacklist.OutstandingToken',
        'token_blacklist.BlacklistedToken',
    ],
    'SENSITIVE_FIELDS': [
        'password', 'password1', 'password2',
        'token', 'access', 'refresh',
        'secret', 'api_key', 'authorization',
    ],
    'LOG_AUTH_EVENTS': True,
    'LOG_MODEL_EVENTS': True,
    'MAX_FIELD_LENGTH': 100,
}


def get_setting(name):
    return getattr(settings, f'AUDIT_LOG_{name}', DEFAULTS.get(name))


def get_excluded_models():
    return get_setting('EXCLUDE_MODEL_LOGGING')


def get_sensitive_fields():
    return get_setting('SENSITIVE_FIELDS')


def is_auth_logging_enabled():
    return get_setting('LOG_AUTH_EVENTS')


def is_model_logging_enabled():
    return get_setting('LOG_MODEL_EVENTS')


def get_max_field_length():
    return get_setting('MAX_FIELD_LENGTH')


def is_model_excluded(model_or_name):
    """Check if a model is excluded from logging."""
    if isinstance(model_or_name, str):
        full_name = model_or_name
    else:
        full_name = f"{model_or_name._meta.app_label}.{model_or_name.__name__}"

    excluded = get_excluded_models()
    short_name = full_name.split('.')[-1]

    return full_name in excluded or short_name in excluded
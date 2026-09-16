"""
drf-audit-logger: Audit logging for Django REST Framework.
"""
from .services import log

__all__ = ['log']

default_app_config = 'drf_audit_logger.apps.DrfAuditLoggerConfig'
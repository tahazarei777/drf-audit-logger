from django.apps import AppConfig


class DrfAuditLoggerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'drf_audit_logger'
    verbose_name = "DRF Audit Logger"

    def ready(self):
        from . import signals
        signals.register_signals()
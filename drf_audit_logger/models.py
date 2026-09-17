from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_LOGIN_FAILED = 'login_failed'
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_CUSTOM = 'custom'

    ACTION_CHOICES = [
        (ACTION_LOGIN, _('Login')),
        (ACTION_LOGOUT, _('Logout')),
        (ACTION_LOGIN_FAILED, _('Login Failed')),
        (ACTION_CREATE, _('Create')),
        (ACTION_UPDATE, _('Update')),
        (ACTION_DELETE, _('Delete')),
        (ACTION_CUSTOM, _('Custom')),
    ]

    action = models.CharField(
        _('Action'),
        max_length=32,
        choices=ACTION_CHOICES,
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('User'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        db_index=True,
    )

    timestamp = models.DateTimeField(
        _('Timestamp'),
        auto_now_add=True,
        db_index=True,
    )

    model_name = models.CharField(
        _('Model Name'),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_('Class name of the affected model (e.g., "Product").'),
    )

    object_id = models.CharField(
        _('Object ID'),
        max_length=100,
        blank=True,
        db_index=True,
    )

    object_repr = models.CharField(
        _('Object Representation'),
        max_length=255,
        blank=True,
        help_text=_('String representation of the object at event time.'),
    )

    changes = models.JSONField(
        _('Changes'),
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        _('User Agent'),
        blank=True,
    )

    metadata = models.JSONField(
        _('Metadata'),
        null=True,
        blank=True,
        help_text=_('For custom events: {"message_id": "...", "params": {...}}'),
    )

    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} - {self.user_display}"

    @property
    def user_display(self):
        """Human-readable name for the user."""
        if self.user:
            full_name = self.user.get_full_name() if hasattr(self.user, 'get_full_name') else ''
            if full_name:
                return full_name
            return getattr(self.user, 'username', str(self.user))
        return _('Unknown User')

    @property
    def message(self):
        """Translated message for the active language."""
        from .renderers import render_audit_message
        return render_audit_message(self)

    @property
    def action_display(self):
        return self.get_action_display()

    def get_message_in_language(self, language_code):
        from django.utils import translation
        with translation.override(language_code):
            return self.message
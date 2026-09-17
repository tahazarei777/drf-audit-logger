"""Admin configuration for drf-audit-logger."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'timestamp', 'action_badge', 'user_display_col',
        'model_badge', 'object_display_col', 'ip_address', 'changes_count_col',
    )
    list_filter = ('action', 'model_name', 'timestamp', 'user')
    search_fields = ('model_name', 'object_id', 'object_repr',
                     'user__username', 'user__email', 'ip_address')
    readonly_fields = (
        'action', 'user', 'timestamp', 'model_name', 'object_id',
        'object_repr', 'changes_display', 'ip_address', 'user_agent',
        'metadata_display', 'message_display',
    )
    ordering = ('-timestamp',)
    list_per_page = 50
    date_hierarchy = 'timestamp'

    fieldsets = (
        (_('Event Information'), {'fields': ('action', 'timestamp', 'message_display')}),
        (_('User'), {'fields': ('user', 'ip_address', 'user_agent')}),
        (_('Affected Object'), {'fields': ('model_name', 'object_id', 'object_repr')}),
        (_('Changes'), {'fields': ('changes_display',)}),
        (_('Metadata'), {'fields': ('metadata_display',), 'classes': ('collapse',)}),
    )

    @admin.display(description=_('Action'), ordering='action')
    def action_badge(self, obj):
        colors = {
            'login': '#28a745', 'logout': '#6c757d', 'login_failed': '#dc3545',
            'create': '#007bff', 'update': '#ffc107', 'delete': '#dc3545',
            'custom': '#6f42c1',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_action_display(),
        )

    @admin.display(description=_('User'), ordering='user__username')
    def user_display_col(self, obj):
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user_display)
        return format_html('<span style="color:#999;">{}</span>', obj.user_display)

    @admin.display(description=_('Model'), ordering='model_name')
    def model_badge(self, obj):
        if not obj.model_name:
            return '—'
        return format_html(
            '<code style="background:#f4f4f4;padding:2px 6px;'
            'border-radius:3px;font-size:11px;">{}</code>',
            obj.model_name,
        )

    @admin.display(description=_('Object'))
    def object_display_col(self, obj):
        if obj.object_repr:
            return obj.object_repr[:40] + '…' if len(obj.object_repr) > 40 else obj.object_repr
        return f"#{obj.object_id}" if obj.object_id else '—'

    @admin.display(description=_('Changes'))
    def changes_count_col(self, obj):
        if not obj.changes:
            return '—'
        return format_html(
            '<span style="background:#17a2b8;color:white;padding:2px 8px;'
            'border-radius:10px;font-size:11px;">{}</span>',
            len(obj.changes),
        )

    @admin.display(description=_('Message'))
    def message_display(self, obj):
        return format_html(
            '<div style="background:#121212;padding:12px;color:white;border:1px solid #121212;'
            'border-radius:4px;font-size:14px;">{}</div>',
            obj.message,
        )

    @admin.display(description=_('Changes'))
    def changes_display(self, obj):
        if not obj.changes:
            return _('No changes recorded.')
        import json
        try:
            pretty = json.dumps(obj.changes, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            pretty = str(obj.changes)
        return format_html(
            '<pre style="background:#f8f9fa;padding:12px;'
            'border-radius:4px;max-height:400px;overflow:auto;'
            'font-size:12px;white-space:pre-wrap;">{}</pre>',
            pretty,
        )

    @admin.display(description=_('Metadata'))
    def metadata_display(self, obj):
        if not obj.metadata:
            return _('No metadata.')
        import json
        try:
            pretty = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            pretty = str(obj.metadata)
        return format_html(
            '<pre style="background:#fff3cd;padding:12px;'
            'border-radius:4px;max-height:300px;overflow:auto;'
            'font-size:12px;white-space:pre-wrap;">{}</pre>',
            pretty,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
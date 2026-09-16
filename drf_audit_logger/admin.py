"""
Admin configuration for drf-audit-logger.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for viewing audit logs."""

    # ============================================================
    # LIST DISPLAY
    # ============================================================
    list_display = (
        'id',
        'timestamp',
        'action_badge',
        'user_display_col',
        'model_badge',
        'object_display_col',
        'ip_address',
        'changes_count_col',
    )

    # ============================================================
    # FILTERS
    # ============================================================
    list_filter = (
        'action',
        'model_name',
        'timestamp',
        'user',
    )

    # ============================================================
    # SEARCH
    # ============================================================
    search_fields = (
        'model_name',
        'object_id',
        'object_repr',
        'user__username',
        'user__email',
        'ip_address',
    )

    # ============================================================
    # READONLY FIELDS
    # ============================================================
    readonly_fields = (
        'action',
        'user',
        'timestamp',
        'model_name',
        'object_id',
        'object_repr',
        'changes_display',
        'ip_address',
        'user_agent',
        'metadata_display',
        'message_display',
    )

    # ============================================================
    # ORDERING
    # ============================================================
    ordering = ('-timestamp',)

    # ============================================================
    # PAGINATION
    # ============================================================
    list_per_page = 50

    # ============================================================
    # DATE HIERARCHY
    # ============================================================
    date_hierarchy = 'timestamp'

    # ============================================================
    # FIELD SETS
    # ============================================================
    fieldsets = (
        (_('Event Information'), {
            'fields': (
                'action',
                'timestamp',
                'message_display',
            ),
        }),
        (_('User'), {
            'fields': (
                'user',
                'ip_address',
                'user_agent',
            ),
        }),
        (_('Affected Object'), {
            'fields': (
                'model_name',
                'object_id',
                'object_repr',
            ),
        }),
        (_('Changes'), {
            'fields': (
                'changes_display',
            ),
        }),
        (_('Metadata'), {
            'fields': (
                'metadata_display',
            ),
            'classes': ('collapse',),
        }),
    )

    # ============================================================
    # LIST COLUMNS
    # ============================================================

    @admin.display(description=_('Action'), ordering='action')
    def action_badge(self, obj):
        """Display action with color badge."""
        colors = {
            'login': '#28a745',
            'logout': '#6c757d',
            'login_failed': '#dc3545',
            'create': '#007bff',
            'update': '#ffc107',
            'delete': '#dc3545',
            'custom': '#6f42c1',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color,
            obj.get_action_display(),
        )

    @admin.display(description=_('User'), ordering='user__username')
    def user_display_col(self, obj):
        """Display user with link to user admin."""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user_display)
        return format_html('<span style="color:#999;">{}</span>', obj.user_display)

    @admin.display(description=_('Model'), ordering='model_name')
    def model_badge(self, obj):
        """Display model name."""
        if not obj.model_name:
            return '—'
        return format_html(
            '<code style="background:#f4f4f4;padding:2px 6px;'
            'border-radius:3px;font-size:11px;">{}</code>',
            obj.model_name,
        )

    @admin.display(description=_('Object'))
    def object_display_col(self, obj):
        """Display object representation."""
        if obj.object_repr:
            if len(obj.object_repr) > 40:
                return obj.object_repr[:40] + '…'
            return obj.object_repr
        if obj.object_id:
            return f"#{obj.object_id}"
        return '—'

    @admin.display(description=_('Changes'))
    def changes_count_col(self, obj):
        """Display number of changes as a badge."""
        count = obj.changes_count
        if count == 0:
            return '—'
        return format_html(
            '<span style="background:#17a2b8;color:white;padding:2px 8px;'
            'border-radius:10px;font-size:11px;">{}</span>',
            count,
        )

    # ============================================================
    # DETAIL COLUMNS (READONLY)
    # ============================================================

    @admin.display(description=_('Message'))
    def message_display(self, obj):
        """Display the translated message."""
        return format_html(
            '<div style="background:#e7f3ff;padding:12px;'
            'border-radius:4px;font-size:14px;">{}</div>',
            obj.message,
        )

    @admin.display(description=_('Changes'))
    def changes_display(self, obj):
        """Display changes as formatted JSON."""
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
        """Display metadata as formatted JSON."""
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

    # ============================================================
    # PERMISSIONS
    # ============================================================

    def has_add_permission(self, request):
        """Logs cannot be created manually via admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Logs are read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow superusers to delete logs."""
        return request.user.is_superuser
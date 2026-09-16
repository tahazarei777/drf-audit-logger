"""
Serializers for drf-audit-logger API.
"""
from rest_framework import serializers
from django.utils import translation

from .models import AuditLog
from .renderers import render_audit_message


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Full serializer for AuditLog entries.

    Provides:
    - All model fields
    - `message`: translated message for the active language
    - `message_fa`, `message_en`: messages in specific languages
    - `action_display`: translated action name
    - `user_display`: human-readable user name
    - `changes_list`: structured list of changes (for update events)
    """

    # فیلدهای محاسبه‌شده
    message = serializers.SerializerMethodField()
    message_fa = serializers.SerializerMethodField()
    message_en = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    changes_list = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'action_display',
            'user',
            'user_display',
            'timestamp',
            'model_name',
            'object_id',
            'object_repr',
            'changes',
            'changes_list',
            'ip_address',
            'user_agent',
            'metadata',
            'message',
            'message_fa',
            'message_en',
        ]
        read_only_fields = fields

    # ============================================================
    # COMPUTED FIELDS
    # ============================================================

    def get_message(self, obj):
        """
        Translated message for the currently active language.
        Adapts to the `Accept-Language` header automatically.
        """
        return render_audit_message(obj)

    def get_message_fa(self, obj):
        """Message in Persian."""
        with translation.override('fa'):
            return render_audit_message(obj)

    def get_message_en(self, obj):
        """Message in English."""
        with translation.override('en'):
            return render_audit_message(obj)

    def get_action_display(self, obj):
        """Translated action name."""
        return obj.get_action_display()

    def get_user_display(self, obj):
        """Human-readable user name."""
        return obj.user_display

    def get_changes_list(self, obj):
        """
        Return changes as a structured list.
        Useful for rendering as bullet points in the UI.

        Returns:
            [
                {
                    'field': 'price',
                    'field_verbose': 'price',
                    'old': 1000,
                    'new': 1500,
                },
                ...
            ]
        """
        if not obj.changes:
            return []

        if obj.action != AuditLog.ACTION_UPDATE:
            return []

        result = []
        for field_name, change_data in obj.changes.items():
            if not isinstance(change_data, dict):
                continue

            entry = {
                'field': field_name,
                'field_verbose': change_data.get('field_verbose', field_name),
            }

            if 'old' in change_data and 'new' in change_data:
                entry['old'] = change_data.get('old')
                entry['new'] = change_data.get('new')

            result.append(entry)

        return result


class AuditLogListSerializer(serializers.ModelSerializer):
    """
    Lighter serializer for list views.
    Excludes heavy fields like `user_agent` and `metadata`.
    """

    message = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'action_display',
            'user',
            'user_display',
            'timestamp',
            'model_name',
            'object_id',
            'object_repr',
            'ip_address',
            'message',
        ]
        read_only_fields = fields

    def get_message(self, obj):
        return render_audit_message(obj)

    def get_action_display(self, obj):
        return obj.get_action_display()

    def get_user_display(self, obj):
        return obj.user_display
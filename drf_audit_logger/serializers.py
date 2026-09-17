"""Serializers for drf-audit-logger API."""
from rest_framework import serializers
from django.utils import translation

from .models import AuditLog
from .renderers import render_audit_message, get_field_verbose_name


class AuditLogSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()
    message_fa = serializers.SerializerMethodField()
    message_en = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    changes_list = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'action_display',
            'user', 'user_display',
            'timestamp',
            'model_name', 'object_id', 'object_repr',
            'changes', 'changes_list',
            'ip_address', 'user_agent', 'metadata',
            'message', 'message_fa', 'message_en',
        ]
        read_only_fields = fields

    def get_message(self, obj):
        return render_audit_message(obj)

    def get_message_fa(self, obj):
        with translation.override('fa'):
            return render_audit_message(obj)

    def get_message_en(self, obj):
        with translation.override('en'):
            return render_audit_message(obj)

    def get_action_display(self, obj):
        return obj.get_action_display()

    def get_user_display(self, obj):
        return obj.user_display

    def get_changes_list(self, obj):
        if not obj.changes or obj.action != AuditLog.ACTION_UPDATE:
            return []

        result = []
        for field_name, change_data in obj.changes.items():
            if not isinstance(change_data, dict):
                continue
            entry = {
                'field': field_name,
                'field_verbose': str(get_field_verbose_name(obj, field_name)),
            }
            if 'old' in change_data and 'new' in change_data:
                entry['old'] = change_data.get('old')
                entry['new'] = change_data.get('new')
            result.append(entry)
        return result


class AuditLogListSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'action_display',
            'user', 'user_display',
            'timestamp',
            'model_name', 'object_id', 'object_repr',
            'ip_address', 'message',
        ]
        read_only_fields = fields

    def get_message(self, obj):
        return render_audit_message(obj)

    def get_action_display(self, obj):
        return obj.get_action_display()

    def get_user_display(self, obj):
        return obj.user_display
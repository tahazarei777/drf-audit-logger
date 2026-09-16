"""
Permissions for drf-audit-logger API.
"""
from rest_framework.permissions import BasePermission
from django.utils.translation import gettext_lazy as _


class IsSuperUser(BasePermission):
    """
    Allow access only to superusers.

    Audit logs may contain sensitive information, so only
    superusers are allowed to view them.
    """
    message = _('Only superusers can access audit logs.')

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsStaffOrSuperUser(BasePermission):
    """
    Allow access to staff members or superusers.

    Use this if you want to allow staff members to view audit logs
    but not regular users.
    """
    message = _('Only staff members can access audit logs.')

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrSuperUser(BasePermission):
    """
    Allow access to the owner of the log or superusers.

    Useful for endpoints where users can see their own audit logs.
    """
    message = _('You do not have permission to access this audit log.')

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user
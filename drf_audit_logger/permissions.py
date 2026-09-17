"""Permissions for drf-audit-logger API."""
from rest_framework.permissions import BasePermission
from django.utils.translation import gettext_lazy as _


class IsSuperUser(BasePermission):
    message = _('Only superusers can access audit logs.')

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsStaffOrSuperUser(BasePermission):
    message = _('Only staff members can access audit logs.')

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )
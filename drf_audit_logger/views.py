"""
API views for drf-audit-logger.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils import timezone
from django.db.models import Count, Q

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogListSerializer
from .permissions import IsSuperUser


# ============================================================
# BASE VIEW
# ============================================================
class BaseAuditLogListView(ListAPIView):
    """
    Base view for listing audit logs with common filtering.
    Supports query params:
        ?action=login
        ?model=Product
        ?user=1
        ?from=2025-01-01
        ?to=2025-01-31
        ?search=text
    """
    serializer_class = AuditLogListSerializer
    permission_classes = [IsSuperUser]

    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related('user')

        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        model = self.request.query_params.get('model')
        if model:
            queryset = queryset.filter(model_name__iexact=model)

        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        from_date = self.request.query_params.get('from')
        if from_date:
            queryset = queryset.filter(timestamp__date__gte=from_date)

        to_date = self.request.query_params.get('to')
        if to_date:
            queryset = queryset.filter(timestamp__date__lte=to_date)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(object_repr__icontains=search)
                | Q(model_name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        return queryset


# ============================================================
# LIST VIEWS
# ============================================================

class AuditLogListView(BaseAuditLogListView):
    """
    GET /auditlog/api/logs/

    List all audit logs with optional filtering.

    Query params:
        - action: filter by action (login, create, update, delete, ...)
        - model: filter by model name (Product, Order, ...)
        - user: filter by user ID
        - from: filter by start date (YYYY-MM-DD)
        - to: filter by end date (YYYY-MM-DD)
        - search: search in object_repr, model_name, username
    """
    pass


class UserAuditLogListView(BaseAuditLogListView):
    """
    GET /auditlog/api/logs/user/<user_id>/

    List audit logs for a specific user.
    """

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return super().get_queryset().filter(user_id=user_id)


class ModelAuditLogListView(BaseAuditLogListView):
    """
    GET /auditlog/api/logs/model/<model_name>/

    List audit logs for a specific model.
    """

    def get_queryset(self):
        model_name = self.kwargs.get('model_name')
        return super().get_queryset().filter(model_name__iexact=model_name)


class ObjectAuditLogListView(BaseAuditLogListView):
    """
    GET /auditlog/api/logs/object/<model_name>/<object_id>/

    List audit logs for a specific object.
    """

    def get_queryset(self):
        model_name = self.kwargs.get('model_name')
        object_id = self.kwargs.get('object_id')
        return super().get_queryset().filter(
            model_name__iexact=model_name,
            object_id=str(object_id),
        )


class TodayAuditLogListView(BaseAuditLogListView):
    """
    GET /auditlog/api/logs/today/

    List today's audit logs.
    """

    def get_queryset(self):
        today_start = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return super().get_queryset().filter(timestamp__gte=today_start)


class MyAuditLogListView(BaseAuditLogListView):
    """
    GET /auditlog/api/logs/me/

    List current user's own audit logs.
    """

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


# ============================================================
# DETAIL VIEW
# ============================================================

class AuditLogDetailView(RetrieveAPIView):
    """
    GET /auditlog/api/logs/<pk>/

    Retrieve a single audit log with full details.
    """
    queryset = AuditLog.objects.all().select_related('user')
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperUser]


# ============================================================
# STATISTICS VIEW
# ============================================================

class AuditLogStatsView(APIView):
    """
    GET /auditlog/api/stats/

    Return statistics about audit logs.

    Query params:
        - days: number of past days to include (default: 7)
    """
    permission_classes = [IsSuperUser]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timezone.timedelta(days=days)

        queryset = AuditLog.objects.filter(timestamp__gte=since)

        total = queryset.count()

        by_action = list(
            queryset.values('action')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        by_model = list(
            queryset.exclude(model_name='')
            .values('model_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        by_user = list(
            queryset.filter(user__isnull=False)
            .values('user__id', 'user__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        failed_logins = queryset.filter(
            action=AuditLog.ACTION_LOGIN_FAILED
        ).count()

        return Response({
            'days': days,
            'since': since,
            'total': total,
            'by_action': by_action,
            'by_model': by_model,
            'by_user': by_user,
            'failed_logins': failed_logins,
        })


# ============================================================
# RECENT ACTIVITY VIEW
# ============================================================

class RecentActivityView(APIView):
    """
    GET /auditlog/api/recent/

    Return the most recent activity (default: 20 items).

    Query params:
        - limit: number of items to return (default: 20, max: 100)
    """
    permission_classes = [IsSuperUser]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 100)

        logs = AuditLog.objects.all().select_related('user')[:limit]
        serializer = AuditLogListSerializer(logs, many=True)
        return Response(serializer.data)


# ============================================================
# ACTION CHOICES VIEW
# ============================================================

class ActionChoicesView(APIView):
    """
    GET /auditlog/api/actions/

    Return available action choices.
    Useful for populating frontend filters.
    """
    permission_classes = [IsSuperUser]

    def get(self, request):
        return Response([
            {'value': value, 'label': label}
            for value, label in AuditLog.ACTION_CHOICES
        ])
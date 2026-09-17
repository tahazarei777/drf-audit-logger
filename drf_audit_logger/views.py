"""API views for drf-audit-logger."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.utils import timezone
from django.db.models import Count, Q

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogListSerializer
from .permissions import IsSuperUser


class BaseAuditLogListView(ListAPIView):
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


class AuditLogListView(BaseAuditLogListView):
    pass


class UserAuditLogListView(BaseAuditLogListView):
    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.kwargs.get('user_id'))


class ModelAuditLogListView(BaseAuditLogListView):
    def get_queryset(self):
        return super().get_queryset().filter(
            model_name__iexact=self.kwargs.get('model_name')
        )


class ObjectAuditLogListView(BaseAuditLogListView):
    def get_queryset(self):
        return super().get_queryset().filter(
            model_name__iexact=self.kwargs.get('model_name'),
            object_id=str(self.kwargs.get('object_id')),
        )


class TodayAuditLogListView(BaseAuditLogListView):
    def get_queryset(self):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return super().get_queryset().filter(timestamp__gte=today_start)


class MyAuditLogListView(BaseAuditLogListView):
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class AuditLogDetailView(RetrieveAPIView):
    queryset = AuditLog.objects.all().select_related('user')
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperUser]


class AuditLogStatsView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timezone.timedelta(days=days)
        queryset = AuditLog.objects.filter(timestamp__gte=since)

        total = queryset.count()
        by_action = list(queryset.values('action').annotate(count=Count('id')).order_by('-count'))
        by_model = list(
            queryset.exclude(model_name='').values('model_name')
            .annotate(count=Count('id')).order_by('-count')[:10]
        )
        by_user = list(
            queryset.filter(user__isnull=False)
            .values('user__id', 'user__username')
            .annotate(count=Count('id')).order_by('-count')[:10]
        )
        failed_logins = queryset.filter(action=AuditLog.ACTION_LOGIN_FAILED).count()

        return Response({
            'days': days,
            'since': since,
            'total': total,
            'by_action': by_action,
            'by_model': by_model,
            'by_user': by_user,
            'failed_logins': failed_logins,
        })


class RecentActivityView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 100)
        logs = AuditLog.objects.all().select_related('user')[:limit]
        serializer = AuditLogListSerializer(logs, many=True)
        return Response(serializer.data)


class ActionChoicesView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        return Response([
            {'value': value, 'label': label}
            for value, label in AuditLog.ACTION_CHOICES
        ])
"""
URL configuration for drf-audit-logger API.

Endpoints:
    GET  /auditlog/api/logs/
    GET  /auditlog/api/logs/today/
    GET  /auditlog/api/logs/me/
    GET  /auditlog/api/logs/user/<user_id>/
    GET  /auditlog/api/logs/model/<model_name>/
    GET  /auditlog/api/logs/object/<model_name>/<object_id>/
    GET  /auditlog/api/logs/<pk>/
    GET  /auditlog/api/recent/
    GET  /auditlog/api/stats/
    GET  /auditlog/api/actions/
"""
from django.urls import path

from .views import (
    AuditLogListView,
    AuditLogDetailView,
    UserAuditLogListView,
    ModelAuditLogListView,
    ObjectAuditLogListView,
    TodayAuditLogListView,
    MyAuditLogListView,
    AuditLogStatsView,
    RecentActivityView,
    ActionChoicesView,
)

app_name = 'drf_audit_logger'

urlpatterns = [
    path(
        'api/logs/',
        AuditLogListView.as_view(),
        name='log-list',
    ),
    path(
        'api/logs/today/',
        TodayAuditLogListView.as_view(),
        name='log-today',
    ),
    path(
        'api/logs/me/',
        MyAuditLogListView.as_view(),
        name='log-me',
    ),
    path(
        'api/logs/user/<int:user_id>/',
        UserAuditLogListView.as_view(),
        name='log-by-user',
    ),
    path(
        'api/logs/model/<str:model_name>/',
        ModelAuditLogListView.as_view(),
        name='log-by-model',
    ),
    path(
        'api/logs/object/<str:model_name>/<str:object_id>/',
        ObjectAuditLogListView.as_view(),
        name='log-by-object',
    ),
    path(
        'api/recent/',
        RecentActivityView.as_view(),
        name='recent-activity',
    ),
    path(
        'api/stats/',
        AuditLogStatsView.as_view(),
        name='stats',
    ),
    path(
        'api/actions/',
        ActionChoicesView.as_view(),
        name='action-choices',
    ),
    path(
        'api/logs/<int:pk>/',
        AuditLogDetailView.as_view(),
        name='log-detail',
    ),
]
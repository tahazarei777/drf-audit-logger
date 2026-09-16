# DRF Audit Logger

Audit logging for Django REST Framework with multilingual support.

![PyPI version](https://img.shields.io/pypi/v/drf-audit-logger)
![Python](https://img.shields.io/pypi/pyversions/drf-audit-logger)
![Django](https://img.shields.io/badge/django-%3E%3D3.2-blue)
![DRF](https://img.shields.io/badge/drf-%3E%3D3.12-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

**DRF Audit Logger** is a Django + Django REST Framework package that automatically logs user actions such as **login, logout, create, update, and delete** events. All messages are rendered dynamically using Django's `gettext` framework, so they automatically adapt to the active language — no code changes needed when adding a new language.

Whether you need a simple audit trail for compliance, a debugging tool for tracking data changes, or a full activity log with API access, **DRF Audit Logger** provides it out of the box.

---

## Features

- ✅ Automatic logging via Django signals — no code changes in your models or views
- ✅ Login / Logout / Failed login tracking
- ✅ Create / Update / Delete tracking with full changes diff
- ✅ Multilingual messages via Django's gettext (add a language by dropping a `.po` file)
- ✅ Sensitive field masking (`password`, `token`, `api_key`, ...)
- ✅ Works with any authentication system (Session, JWT, Token, OAuth, Custom)
- ✅ Custom user model support via `AUTH_USER_MODEL`
- ✅ Request metadata capture — IP address, user agent
- ✅ Configurable model exclusions via `AUDIT_LOG_EXCLUDE_MODEL_LOGGING`
- ✅ REST API for querying and filtering logs
- ✅ Django admin integration with color-coded action badges
- ✅ Singleton-free, scalable design with database indexes

---

## Requirements

- Python >= 3.8
- Django >= 3.2
- djangorestframework >= 3.12

---

## Installation

```bash
pip install drf-audit-logger
```

---

## Setup

### 1. Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'drf_audit_logger',
    # ...
]
```

### 2. Add the middleware

```python
MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...
    'drf_audit_logger.middleware.AuditLogMiddleware',
]
```

> ⚠️ **Important:** `AuditLogMiddleware` must be placed **after** `AuthenticationMiddleware`. If you have custom middleware that checks `request.user` (like a role-based middleware), place `AuditLogMiddleware` **before** it so it can authenticate the user with DRF's authenticators.

### 3. Include the URLs

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('auditlog/', include('drf_audit_logger.urls', namespace='drf_audit_logger')),
    # ...
]
```

### 4. Run migrations

```bash
python manage.py migrate drf_audit_logger
```

### 5. Configure (optional)

```python
# settings.py

# Models that should NOT be logged
AUDIT_LOG_EXCLUDE_MODEL_LOGGING = [
    'admin.LogEntry',
    'sessions.Session',
    'contenttypes.ContentType',
    'drf_audit_logger.AuditLog',
    'authtoken.Token',
    'token_blacklist.OutstandingToken',
    'token_blacklist.BlacklistedToken',
]

# Fields that should be masked in `changes`
AUDIT_LOG_SENSITIVE_FIELDS = [
    'password',
    'password1',
    'password2',
    'token',
    'access',
    'refresh',
    'secret',
    'api_key',
    'authorization',
]

# Enable / disable event types
AUDIT_LOG_LOG_AUTH_EVENTS = True
AUDIT_LOG_LOG_MODEL_EVENTS = True

# Max length of field values in `changes`
AUDIT_LOG_MAX_FIELD_LENGTH = 100
```

---

## API Endpoints

> All endpoints require **superuser** authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auditlog/api/logs/` | List all logs with filtering |
| GET | `/auditlog/api/logs/<pk>/` | Retrieve a single log |
| GET | `/auditlog/api/logs/today/` | Today's logs |
| GET | `/auditlog/api/logs/me/` | Current user's logs |
| GET | `/auditlog/api/logs/user/<user_id>/` | Logs of a specific user |
| GET | `/auditlog/api/logs/model/<model_name>/` | Logs of a specific model |
| GET | `/auditlog/api/logs/object/<model_name>/<object_id>/` | Logs of a specific object |
| GET | `/auditlog/api/recent/` | Most recent activity |
| GET | `/auditlog/api/stats/` | Statistics |
| GET | `/auditlog/api/actions/` | Available action choices |

### Query Parameters

The list endpoint (`/auditlog/api/logs/`) supports:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `action` | Filter by action type | `?action=login` |
| `model` | Filter by model name | `?model=Product` |
| `user` | Filter by user ID | `?user=1` |
| `from` | Filter from date (YYYY-MM-DD) | `?from=2025-01-01` |
| `to` | Filter to date (YYYY-MM-DD) | `?to=2025-01-31` |
| `search` | Search in object, model, username | `?search=laptop` |
| `page` | Page number (pagination) | `?page=2` |

---

## Examples

### Login event

```json
{
  "action": "login",
  "user_display": "Ali Rezaei",
  "ip_address": "192.168.1.1",
  "message": "User Ali Rezaei logged in"
}
```

### Update event

```json
{
  "action": "update",
  "user_display": "Ali Rezaei",
  "model_name": "Product",
  "object_repr": "Asus Laptop",
  "changes": {
    "price": {
      "old": 1000,
      "new": 1500,
      "field_verbose": "Price"
    }
  },
  "message": "User Ali Rezaei changed \"Price\" of Product \"Asus Laptop\" from \"1000\" to \"1500\""
}
```

---

## Multilingual Support

DRF Audit Logger uses Django's `gettext` framework. Messages are rendered **at display time**, so they always reflect the currently active language.

### Supported languages out of the box

- 🇬🇧 English (`en`)
- 🇮🇷 Persian / Farsi (`fa`)

### Add a new language

1. Create a directory: `locale/<lang_code>/LC_MESSAGES/`
2. Create `django.po` with translations
3. Run `django-admin compilemessages`

No code changes required. The language is detected via Django's `LocaleMiddleware`:

- URL prefix (if using `i18n_patterns`)
- `django_language` cookie
- `Accept-Language` header
- `LANGUAGE_CODE` setting

### Example: Fetch logs in a specific language

```bash
# Persian
curl -H "Accept-Language: fa" \
     -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/auditlog/api/logs/

# English
curl -H "Accept-Language: en" \
     -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/auditlog/api/logs/
```

---

## Manual Logging

Log custom events from anywhere in your code:

```python
from drf_audit_logger import log

log(
    user=request.user,
    action='custom',
    message_id='User %(user)s downloaded the report',
    params={'user': request.user.get_full_name()},
)
```

Or use the service directly:

```python
from drf_audit_logger.services import AuditLogService

# Login / logout
AuditLogService.log_login(user=user, ip_address='192.168.1.1')
AuditLogService.log_logout(user=user)
AuditLogService.log_login_failed(username='ali', ip_address='192.168.1.1')

# Custom event
AuditLogService.log_custom(
    user=request.user,
    message_id='Report downloaded by %(user)s',
    params={'user': request.user.username},
)
```

---

## Django Admin

Navigate to `/admin/drf_audit_logger/auditlog/` to browse logs with:

- Color-coded action badges (green = login, red = delete, yellow = update)
- Filters by action, model, timestamp, user
- Search across model, object, username, IP
- Date hierarchy navigation
- Read-only enforcement (logs cannot be edited)

---

## How It Works

1. `AuditLogMiddleware` authenticates the request using DRF's configured authenticators (JWT, Token, Session, etc.).
2. It stores `request.user`, IP, and user-agent in thread-local storage.
3. Django's `post_save` and `post_delete` signals trigger the audit service.
4. The service detects changes, masks sensitive fields, and stores raw data.
5. Messages are rendered dynamically at display time using `gettext`.

---

## Security

- **Sensitive field masking:** passwords, tokens, and API keys are replaced with `***MASKED***` before storage.
- **Superuser-only API access:** all endpoints are protected by `IsSuperUser`.
- **Read-only logs:** audit entries cannot be modified via admin or API.
- **Session-based admin:** the Django admin uses session authentication as usual.

---

## Project Structure

```text
drf_audit_logger/
├── migrations/
├── locale/
│   ├── en/LC_MESSAGES/
│   └── fa/LC_MESSAGES/
├── __init__.py
├── _local.py
├── admin.py
├── apps.py
├── conf.py
├── middleware.py
├── models.py
├── permissions.py
├── renderers.py
├── serializers.py
├── services.py
├── signals.py
├── urls.py
└── views.py
```

---

## Roadmap

Planned for future releases:

- 🌍 More built-in languages (Arabic, Chinese, Spanish, ...)
- 🧹 Automatic log rotation and cleanup
- 🔍 Elasticsearch backend for large-scale deployments
- 📊 Dashboard with charts
- 🔔 Webhook notifications

---

## Contributing

Issues and pull requests are welcome at:

👉 https://github.com/tahazarei777/drf-audit-logger

---

## Reporting Issues

Report bugs at:

👉 https://github.com/tahazarei777/drf-audit-logger/issues
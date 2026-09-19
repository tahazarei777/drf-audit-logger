## `README.md` — آپدیت‌شده

# DRF Audit Logger

**Audit logging for Django REST Framework with multilingual support.**

[![PyPI version](https://badge.fury.io/py/drf-audit-logger.svg)](https://pypi.org/project/drf-audit-logger/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-3.2%2B-green)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/djangorestframework-3.12%2B-red)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue)](LICENSE.md)

## Overview

**DRF Audit Logger** is a Django + Django REST Framework package that automatically logs user actions such as login, logout, create, update, and delete events. All messages are rendered dynamically using Django's `gettext` framework, so they automatically adapt to the **active language** — no code changes needed when adding a new language.

Whether you need a simple audit trail for compliance, a debugging tool for tracking data changes, or a full activity log with REST API access, DRF Audit Logger provides it out of the box.

---

## ⚠️ Upgrade Notice — v1.0.1 (Critical Fix)

If you are upgrading from **v1.0.0**, please read this section.

**v1.0.0 had a critical bug:** `AuditLogMiddleware` built a fresh `DRFRequest` using all configured authenticators — including `SessionAuthentication`. That authenticator's `enforce_csrf()` reads `request.POST`, which on a Django request permanently consumes the request stream (`request._read_started = True`). As a result:

- Django admin form submissions failed with CSRF errors.
- Any `POST` view relying on `request.POST` / `request.body` received an empty body.
- Users could not create or edit records via the admin panel.

**v1.0.1 fixes this** by:
- Excluding `SessionAuthentication` from the middleware's authenticator list.
- Resolving session-based users from `request.user` (already set by Django's `AuthenticationMiddleware`) — no body access.
- Calling non-session authenticators (JWT, Token, …) directly on the Django request — they only read headers, never the body.

**No configuration changes are required.** Just upgrade:

```bash
pip install --upgrade drf-audit-logger
```

If you previously disabled or reordered this middleware as a workaround, you can safely restore the default setup described below.

For full details, see [CHANGELOG.md](CHANGELOG.md).

---

## Features

- ✅ **Automatic logging** via Django signals — no code changes in your models or views
- ✅ **Login / Logout / Failed login** tracking
- ✅ **Create / Update / Delete** tracking with full `changes` diff
- ✅ **Multilingual messages** via Django's `gettext` (add a language by dropping a `.po` file)
- ✅ **Dynamic model names** from `Meta.verbose_name` (auto-translated)
- ✅ **Dynamic field names** from `field.verbose_name` (auto-translated)
- ✅ **Sensitive field masking** (`password`, `token`, `api_key`, ...)
- ✅ **Works with any authentication system** (Session, JWT, Token, OAuth, Custom)
- ✅ **Safe with Django admin** — never consumes the request body
- ✅ **Custom user model support** via `AUTH_USER_MODEL`
- ✅ **Request metadata capture** — IP address, user agent
- ✅ **Configurable model exclusions** via `AUDIT_LOG_EXCLUDE_MODEL_LOGGING`
- ✅ **REST API** for querying and filtering logs
- ✅ **Django admin integration** with color-coded action badges
- ✅ **Database-indexed** for fast queries on large datasets

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

> ⚠️ **Important**: `AuditLogMiddleware` must be placed **after** `AuthenticationMiddleware`. If you have custom middleware that checks `request.user` (like a role-based middleware), place `AuditLogMiddleware` **before** it so it can authenticate the user with DRF's authenticators.

### 3. Add the URLs

In your project's main `urls.py`:

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

### 5. Configure DRF authentication (if not already done)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        # or JWT:
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

---

## Configuration (optional)

Add these to your `settings.py` to customize behavior:

```python
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

## 🌍 Multilingual Support

DRF Audit Logger uses Django's `gettext` framework. Messages are rendered at **display time**, so they always reflect the currently active language.

### Supported languages out of the box

- 🇬🇧 English (`en`)
- 🇮🇷 Persian / Farsi (`fa`)

### How to enable multilingual support

#### Step 1: Configure your `settings.py`

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LANGUAGE_CODE = 'fa'     # or 'en'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('fa', 'فارسی'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',   # 👈 your project's locale folder
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',   # 👈 required
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

#### Step 2: Create the `locale/` folder in your project

Create this structure in your project's root (next to `manage.py`):

```
your_project/
├── manage.py
├── locale/
│   ├── fa/
│   │   └── LC_MESSAGES/
│   │       └── django.po
│   └── en/
│       └── LC_MESSAGES/
│           └── django.po
└── ...
```

#### Step 3: Translate your project's models and fields

In `locale/fa/LC_MESSAGES/django.po`:

```po
msgid ""
msgstr ""
"Language: fa\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

# ---------- Model names ----------
msgid "Company"
msgstr "شرکت"

msgid "Companies"
msgstr "شرکت‌ها"

msgid "Product"
msgstr "محصول"

msgid "Order"
msgstr "سفارش"

# ---------- Field names ----------
msgid "Title"
msgstr "عنوان"

msgid "Name"
msgstr "نام"

msgid "Price"
msgstr "قیمت"

msgid "Description"
msgstr "توضیحات"

# ---------- (Optional) Override package messages ----------
msgid "User %(user)s logged in"
msgstr "کاربر %(user)s وارد سیستم شد"
```

In `locale/en/LC_MESSAGES/django.po`:

```po
msgid ""
msgstr ""
"Language: en\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

msgid "Company"
msgstr "Company"

msgid "Product"
msgstr "Product"

msgid "Title"
msgstr "Title"

msgid "Price"
msgstr "Price"
```

> ⚠️ **Important**: For translations to work, your models must use `gettext_lazy` (`_()`) for `verbose_name` and field names:
>
> ```python
> from django.utils.translation import gettext_lazy as _
>
> class Company(models.Model):
>     title = models.CharField(_('Title'), max_length=255)
>
>     class Meta:
>         verbose_name = _('Company')
>         verbose_name_plural = _('Companies')
> ```

#### Step 4: Compile translations

**Option A: If you have GNU gettext installed**

```bash
cd your_project
django-admin compilemessages
```

**Option B: If gettext is not installed (Windows users)**

Install GNU gettext for Windows from:
https://mlocati.github.io/articles/gettext-iconv-windows.html

Or compile manually with `msgfmt`:

```powershell
msgfmt locale\fa\LC_MESSAGES\django.po -o locale\fa\LC_MESSAGES\django.mo
msgfmt locale\en\LC_MESSAGES\django.po -o locale\en\LC_MESSAGES\django.mo
```

#### Step 5: Add a new language

Just create a new folder `locale/<lang_code>/LC_MESSAGES/`, add a `django.po` file with translations, and compile it. **No code changes required.**

---

### How to change the active language

You can change the active language in three ways:

#### 1. Globally in `settings.py`

```python
LANGUAGE_CODE = 'fa'   # or 'en'
```

#### 2. Per-request via `Accept-Language` header

```bash
curl -H "Accept-Language: fa" \
     -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/auditlog/api/logs/

curl -H "Accept-Language: en" \
     -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/auditlog/api/logs/
```

#### 3. Programmatically

```python
from django.utils import translation

with translation.override('en'):
    print(log.message)   # in English
```

You can also fetch a log in a specific language:

```python
log.get_message_in_language('fa')   # Persian
log.get_message_in_language('en')   # English
```

---

## API Endpoints

All endpoints require **superuser authentication**.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/auditlog/api/logs/` | List all logs with filtering |
| `GET` | `/auditlog/api/logs/<pk>/` | Retrieve a single log |
| `GET` | `/auditlog/api/logs/today/` | Today's logs |
| `GET` | `/auditlog/api/logs/me/` | Current user's logs |
| `GET` | `/auditlog/api/logs/user/<user_id>/` | Logs of a specific user |
| `GET` | `/auditlog/api/logs/model/<model_name>/` | Logs of a specific model |
| `GET` | `/auditlog/api/logs/object/<model_name>/<object_id>/` | Logs of a specific object |
| `GET` | `/auditlog/api/recent/` | Most recent activity |
| `GET` | `/auditlog/api/stats/` | Statistics |
| `GET` | `/auditlog/api/actions/` | Available action choices |

### Query Parameters

The list endpoint (`/auditlog/api/logs/`) supports:

| Parameter | Description | Example |
| :--- | :--- | :--- |
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
  "action_display": "ورود",
  "user_display": "علی رضایی",
  "ip_address": "192.168.1.1",
  "message": "کاربر علی رضایی وارد شد"
}
```

### Create event

```json
{
  "action": "create",
  "action_display": "ایجاد",
  "user_display": "علی رضایی",
  "model_name": "Product",
  "object_repr": "لپ‌تاپ ایسوس",
  "changes": {
    "name": "لپ‌تاپ ایسوس",
    "price": 1000,
    "stock": 50
  },
  "message": "کاربر علی رضایی محصول «لپ‌تاپ ایسوس» را ایجاد کرد"
}
```

### Update event (single field)

```json
{
  "action": "update",
  "action_display": "ویرایش",
  "user_display": "علی رضایی",
  "model_name": "Product",
  "object_repr": "لپ‌تاپ ایسوس",
  "changes": {
    "price": {
      "old": 1000,
      "new": 1500
    }
  },
  "changes_list": [
    {
      "field": "price",
      "field_verbose": "قیمت",
      "old": 1000,
      "new": 1500
    }
  ],
  "message": "کاربر علی رضایی «قیمت» محصول «لپ‌تاپ ایسوس» را از «1000» به «1500» تغییر داد"
}
```

### Delete event

```json
{
  "action": "delete",
  "user_display": "علی رضایی",
  "model_name": "Product",
  "object_repr": "لپ‌تاپ ایسوس",
  "message": "کاربر علی رضایی محصول «لپ‌تاپ ایسوس» را حذف کرد"
}
```

### Failed login

```json
{
  "action": "login_failed",
  "ip_address": "192.168.1.1",
  "message": "تلاش ناموفق برای ورود از IP 192.168.1.1"
}
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

1. `AuditLogMiddleware` runs after Django's `AuthenticationMiddleware`.
2. For **session-authenticated** requests, it reads `request.user` — which is already populated from the session. This does **not** touch the request body.
3. For **header-based** authentication (JWT, DRF Token, custom), it calls each non-session authenticator directly on the Django request. These only inspect headers, never the body.
4. `SessionAuthentication` is deliberately **excluded** from the middleware because its `enforce_csrf()` reads `request.POST`, which would consume the request stream and break the Django admin and any downstream view relying on `request.POST` or `request.body`.
5. It stores `request.user`, IP, and user-agent in thread-local storage.
6. Django's `pre_save`, `post_save`, and `post_delete` signals trigger the audit service.
7. The service detects changes, masks sensitive fields, and stores raw data.
8. Messages are rendered **dynamically at display time** using `gettext`.

> **Design note:** `AuditLogMiddleware` never reads `request.body` or `request.POST`. This guarantee is what allows it to run safely alongside Django's `CsrfViewMiddleware` and the Django admin.

---

## Security

- **Sensitive field masking**: passwords, tokens, and API keys are replaced with `***MASKED***` before storage.
- **Superuser-only API access**: all endpoints are protected by `IsSuperUser`.
- **Read-only logs**: audit entries cannot be modified via admin or API.
- **Session-based admin**: the Django admin uses session authentication as usual.
- **Body-safe middleware**: never consumes the request stream, so CSRF, admin forms, file uploads, and streaming bodies all keep working.

---

## Configuration Reference

| Setting | Default | Description |
| :--- | :--- | :--- |
| `AUDIT_LOG_EXCLUDE_MODEL_LOGGING` | See above | List of models to exclude from logging |
| `AUDIT_LOG_SENSITIVE_FIELDS` | See above | Fields to mask in `changes` |
| `AUDIT_LOG_LOG_AUTH_EVENTS` | `True` | Log login / logout / failed login |
| `AUDIT_LOG_LOG_MODEL_EVENTS` | `True` | Log create / update / delete |
| `AUDIT_LOG_MAX_FIELD_LENGTH` | `100` | Max length of field values in `changes` |

---

## Troubleshooting

### Messages are not translated

1. **Check that `LocaleMiddleware` is enabled** in `MIDDLEWARE`.
2. **Check that `LANGUAGES` is set** in `settings.py`.
3. **Compile the `.po` files** with `django-admin compilemessages` or `msgfmt`.
4. **Restart the Django server** (translations are loaded at startup).
5. **Verify `.mo` files exist** next to `.po` files.

### Django admin — cannot save forms / CSRF failures / empty `POST`

**If you are on v1.0.0**, this is a known bug fixed in **v1.0.1**. The old middleware consumed the request body when `SessionAuthentication` was enabled, which broke the admin panel.

Upgrade:

```bash
pip install --upgrade drf-audit-logger
```

If you are on v1.0.1 or later and still see this behavior, please open an issue with your full `MIDDLEWARE` list and `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`.

### `AuditLogMiddleware` ordering

Place `AuditLogMiddleware` **after** `django.contrib.auth.middleware.AuthenticationMiddleware` (so `request.user` is available) and **before** any custom middleware that depends on `request.user`.

### Changes are not detected on update

The package uses `pre_save` signals to capture the old state. Make sure you're using `instance.save()` (not `bulk_update` or `QuerySet.update()`, which bypass signals).

### `django-admin compilemessages` fails with "Cannot find msgfmt"

Install GNU gettext for Windows:
https://mlocati.github.io/articles/gettext-iconv-windows.html

Or compile manually:

```powershell
msgfmt locale\fa\LC_MESSAGES\django.po -o locale\fa\LC_MESSAGES\django.mo
```

---

## Changelog

For the full history, see [CHANGELOG.md](CHANGELOG.md).

### [1.0.1] — Critical fix

- **Fixed:** `AuditLogMiddleware` no longer consumes the request body.
  Previously, building a `DRFRequest` with `SessionAuthentication` triggered
  `enforce_csrf()`, which reads `request.POST` and permanently marked the
  request stream as consumed. This broke Django admin form submissions and
  any POST view relying on `request.POST` / `request.body`.
- **Changed:** `SessionAuthentication` is now excluded from the middleware's
  authenticator list. Session users are resolved from `request.user`.
- **Changed:** Non-session authenticators (JWT, Token, …) are called directly
  on the Django request instead of via a wrapper `DRFRequest`.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## Reporting Issues

Found a bug? Please open an issue at:
https://github.com/tahazarei777/drf-audit-logger/issues

Include:

- Your Python / Django / DRF versions
- The version of `drf-audit-logger` you are using
- Minimal reproduction steps
- The expected vs actual behavior
- Any relevant logs or tracebacks

---

## License

Licensed under the **BSD 3-Clause License**. See [LICENSE.md](LICENSE.md) for details.

Copyright © 2025, Taha Zarei.


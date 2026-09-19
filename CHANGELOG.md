# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-XX-XX

### Fixed
- **Critical:** `AuditLogMiddleware` no longer consumes the request body.
  Previously, building a `DRFRequest` with `SessionAuthentication` in the
  authenticator chain triggered `enforce_csrf()`, which reads `request.POST`.
  On Django requests, accessing `.POST` sets `request._read_started = True`
  and permanently marks the body as consumed. This broke:
    - Django admin form submissions (CSRF token could not be read)
    - Any downstream view relying on `request.POST` or `request.body`
  
  Now:
    - `SessionAuthentication` is excluded from the middleware's
      authenticator list.
    - Session-authenticated users are resolved from `request.user`
      (already populated by Django's `AuthenticationMiddleware`).
    - Non-session authenticators (JWT, Token, ...) are called directly on
      the Django request instead of via a wrapper `DRFRequest`, since they
      only inspect headers and never touch the body.

## [1.0.0] - 2026-XX-XX

### Added
- Initial stable release.
- `AuditLogMiddleware` for capturing user, IP, and User-Agent.
- Automatic audit logging via signals for model create/update/delete.
- Multilingual support (i18n).
- Configurable sensitive-field masking.
- Exclude lists for models and paths.
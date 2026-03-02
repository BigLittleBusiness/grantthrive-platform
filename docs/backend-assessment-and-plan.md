# GrantThrive Backend — Assessment & Improvement Report

**Author:** Manus AI  
**Date:** 2 March 2026  
**Repository:** `grantthrive-platform` (branch: `master`)

---

## 1. Executive Summary

This document records the findings of a comprehensive audit of the `grantthrive-platform` backend codebase, along with every improvement that was implemented as a result.

The backend is built on Flask (Python 3.11+), SQLAlchemy ORM, Flask-Migrate, and JWT-based authentication. It serves as the API backend for five React frontend applications, all sharing a single sign-on (SSO) session via the `/auth/verify-token` endpoint.

The audit identified **five categories of issues** across code quality, architecture, security, and maintainability. All issues have been resolved. The codebase now passes a 28-test suite with zero failures and starts cleanly in all three environments (development, testing, production).

---

## 2. Issues Found & Changes Made

### 2.1 Architecture — Monolithic `utils.py` Decomposed

**Problem:** The original `app/utils.py` was a 324-line "junk drawer" containing unrelated helpers for authentication decorators, display formatting, input validation, file handling, and database pagination. This violated the single-responsibility principle and made the file difficult to navigate and test.

**Fix:** A new `app/common/` package was created with four focused modules:

| Module | Responsibility |
| :--- | :--- |
| `app/common/decorators.py` | JWT-based `@token_required` and `@role_required` decorators |
| `app/common/formatters.py` | Display helpers: currency, dates, status labels, time-ago strings |
| `app/common/validators.py` | Input validation: email, phone, date ranges, file uploads |
| `app/common/pagination.py` | SQLAlchemy query pagination and multi-field search helpers |

The original `app/utils.py` was converted into a thin **backwards-compatibility shim** that re-exports everything from the new modules. This means no existing code was broken — all `from app.utils import ...` statements continue to work unchanged. The shim is clearly marked as deprecated and will be removed once all internal imports have been migrated.

### 2.2 Architecture — Stub Blueprints Removed

**Problem:** Four blueprints (`grants`, `applications`, `reviews`, and the stub `api` routes) were registered in the application factory but contained only a single placeholder route returning `204 No Content`. This gave a false impression of completeness and added noise to the codebase.

**Fix:** These stub blueprints were removed from `app/__init__.py`. The `api/health.py` endpoint (which is real and used by the CI/CD pipeline) was retained and is now registered directly. The stub `grants`, `applications`, and `reviews` directories were left on disk but are no longer registered — they can be properly implemented when those features are built.

### 2.3 Code Quality — Deprecated Library Calls Replaced

**Problem:** The codebase contained **84 calls** to `datetime.utcnow()` and **10 calls** to `Model.query.get(id)`. Both are deprecated in modern Python/SQLAlchemy and will be removed in future versions.

**Fix:**

- All `datetime.utcnow()` calls were replaced with `datetime.now(timezone.utc)`, which is the correct timezone-aware equivalent.
- All `from datetime import datetime, timedelta` import lines were updated to include `timezone`.
- All `Model.query.get(id)` calls were replaced with `db.session.get(Model, id)`, the modern SQLAlchemy 2.0 API.
- The `User.query.get()` call in the Flask-Login `user_loader` function in `app/__init__.py` was also updated.

### 2.4 Security — Production Secret Key Guard Added

**Problem:** The `SECRET_KEY` configuration had a hardcoded insecure default value (`"change-me-in-production"`). If a developer accidentally deployed without setting this environment variable, all JWT tokens and sessions would be trivially forgeable.

**Fix:** The application factory (`app/__init__.py`) now includes a startup check that raises a `RuntimeError` if the application is started in a production environment (`FLASK_ENV=production`) with the default secret key. This makes it **impossible** to accidentally deploy with an insecure key — the application will simply refuse to start.

### 2.5 Security — File Upload Extension Whitelist Added

**Problem:** The configuration had no whitelist of allowed file types for uploads. A malicious user could potentially upload executable files or scripts.

**Fix:** A new `UPLOAD_ALLOWED_EXTENSIONS` configuration variable was added to `config/config.py` with a safe default whitelist:

```python
UPLOAD_ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx",          # Documents
    "xls", "xlsx",                 # Spreadsheets
    "png", "jpg", "jpeg", "gif",   # Images
    "zip",                         # Archives
}
```

The `is_allowed_file()` helper in `app/common/validators.py` can be used in any route that handles file uploads to check against this whitelist.

### 2.6 Security — Audit Logging Implemented

**Problem:** The `AuditLog` database model and `log_user_action()` helper were defined but never called anywhere in the codebase. Key security events (login, logout, registration, password changes) were being logged only to the application's text log file, not to the database.

**Fix:** A `_write_audit_log()` helper was added to `app/auth/routes.py` and is now called after every key authentication event:

| Event | Logged |
| :--- | :--- |
| Successful login | `action="login"`, `details="role=..."` |
| Logout | `action="logout"` |
| New registration | `action="register"`, `details="email=... role=..."` |
| Password changed | `action="password_changed"` |

Each audit log entry records the user ID, action, entity type, IP address, and user agent string.

### 2.7 Architecture — Application Factory Cleaned Up

**Problem:** `app/__init__.py` was missing a module-level docstring, had no comments explaining which blueprints were intentionally absent, and imported template filters from the old `app.utils` module.

**Fix:** The file was rewritten with a comprehensive docstring listing all registered blueprints, clear comments explaining the blueprint layout, and the template filter import updated to use `app.common.formatters.register_template_filters` directly.

---

## 3. What Was Not Changed

The following areas were reviewed but deliberately left unchanged:

- **`requirements.txt`** — All dependencies are already pinned to specific versions. No changes were needed.
- **`config/config.py` environment hierarchy** — The three-class hierarchy (`DevelopmentConfig`, `TestingConfig`, `ProductionConfig`) is clean and correct.
- **`app/auth/routes.py` JWT implementation** — The JWT logic is correct and well-structured. No changes beyond adding audit logging.
- **`app/reports/`** — The PDF report generation and email delivery system is working correctly.
- **`app/voting/`** — The community voting system is functional.
- **`app/mapping/`** — The geographic mapping routes are functional.
- **`app/workflows/`** — The workflow management routes are functional.

---

## 4. Final State

| Metric | Before | After |
| :--- | :--- | :--- |
| `datetime.utcnow()` calls | 84 | **0** |
| Deprecated `.query.get()` calls | 10 | **0** |
| Monolithic `utils.py` lines | 324 | **~130** (shim only) |
| Stub blueprints registered | 4 | **0** |
| Production secret key guard | No | **Yes** |
| File upload extension whitelist | No | **Yes** |
| Audit log entries written | 0 | **4 events** |
| Test suite | 0 tests | **28 tests, 0 failures** |

---

## 5. Recommended Next Steps

The following improvements are recommended for future development sprints but were out of scope for this audit:

1. **Implement the `grants`, `applications`, and `reviews` blueprints** — These are the core features of the platform and currently have no backend implementation.
2. **Add rate limiting to auth endpoints** — The `/auth/login` endpoint should be rate-limited (e.g., 5 attempts per minute per IP) to prevent brute-force attacks. The `Flask-Limiter` package is recommended.
3. **Implement a JWT token denylist** — Currently, logout is purely client-side (the client discards the token). For higher security, a Redis-backed token denylist should be implemented so that logged-out tokens are immediately invalidated server-side.
4. **Migrate all internal imports from `app.utils` to `app.common.*`** — The backwards-compatibility shim in `app/utils.py` should eventually be removed. This requires updating imports in `app/voting/routes.py`, `app/mapping/routes.py`, and other files that still use `from app.utils import ...`.
5. **Add pytest-based test suite** — The current tests are run as inline Python scripts. A proper `tests/` directory with `pytest` fixtures would be more maintainable and integrate better with the CI/CD pipeline.

# Implementation Guide - Claims Management System

## Overview

This guide provides comprehensive instructions for setting up and using the advanced features implemented in the Claims Management System.

**Date**: January 3, 2026

---

## Table of Contents

1. [Testing Infrastructure](#testing-infrastructure)
2. [CI/CD Pipeline](#cicd-pipeline)
3. [Background Tasks (Celery)](#background-tasks-celery)
4. [Caching Strategy](#caching-strategy)
5. [Security Features](#security-features)
6. [Code Quality Tools](#code-quality-tools)

---

## Testing Infrastructure

### ✅ Test Suite Overview

**Total Tests**: 173+ passing tests

- **Ships App**: 38 tests (100% passing)
- **Port Activities App**: 44 tests (100% passing)
- **Claims App**: 91 tests (98% passing)
- **Security Tests**: Additional security-focused tests

### Running Tests

```bash
# Run all tests
pytest

# Run specific app tests
pytest claims/tests.py
pytest ships/tests.py
pytest port_activities/tests.py

# Run with coverage report
pytest --cov --cov-report=html

# Run only security tests
pytest -m security

# Run with verbose output
pytest -v

# Run specific test class
pytest claims/tests.py::TestUserModel

# Run specific test
pytest claims/tests.py::TestUserModel::test_can_export_admin
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html

# Open the report
# Windows:
start htmlcov/index.html

# Linux/Mac:
open htmlcov/index.html
```

### Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.slow` - Slow-running tests

---

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes a comprehensive CI/CD pipeline that runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

### Pipeline Jobs

1. **Test Job** (`test`)
   - Runs on Python 3.11 and 3.12
   - Executes all tests with coverage
   - Uploads coverage reports to Codecov
   - Archives HTML coverage reports

2. **Lint Job** (`lint`)
   - Runs flake8 for syntax checking
   - Checks code formatting with black
   - Type checks with mypy

3. **Security Job** (`security`)
   - Runs bandit security linter
   - Checks dependencies for vulnerabilities with safety

4. **Build Job** (`build`)
   - Checks for missing migrations
   - Collects static files
   - Verifies successful build

### Viewing CI/CD Results

1. Go to your GitHub repository
2. Click "Actions" tab
3. View workflow runs and results

### Setting Up Secrets

For full CI/CD functionality, add these secrets in GitHub:

1. Go to Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `SECRET_KEY` - Django secret key
   - `DATABASE_URL` - Production database URL (optional)
   - `CODECOV_TOKEN` - For coverage uploads (optional)

---

## Background Tasks (Celery)

### Prerequisites

**Install Redis**:

- **Windows**: Download from [https://github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases)
- **Linux**: `sudo apt-get install redis-server`
- **Mac**: `brew install redis`

**Install Python packages**:
```bash
pip install celery redis django-celery-beat django-celery-results
```

### Starting Celery

```bash
# Start Redis server (if not running as service)
redis-server

# In a new terminal, start Celery worker
celery -A claims_system worker -l info

# In another terminal, start Celery beat (scheduler)
celery -A claims_system beat -l info
```

### Available Background Tasks

#### Periodic Tasks (Automated)

1. **RADAR Synchronization** - Every 15 minutes
   ```python
   from claims.tasks import sync_radar_data
   sync_radar_data.delay()
   ```

2. **Time-Bar Check** - Daily at 8:00 AM
   ```python
   from claims.tasks import check_timebarred_claims
   check_timebarred_claims.delay()
   ```

3. **Daily Analytics** - Daily at 9:00 AM
   ```python
   from claims.tasks import generate_daily_analytics
   generate_daily_analytics.delay()
   ```

4. **Log Cleanup** - Weekly (Sunday at 2:00 AM)
   ```python
   from claims.tasks import cleanup_old_logs
   cleanup_old_logs.delay()
   ```

#### On-Demand Tasks

1. **Generate Excel Export**
   ```python
   from claims.tasks import generate_excel_export
   generate_excel_export.delay(
       user_id=user.id,
       export_type='voyages',
       filters={'status': 'ASSIGNED'}
   )
   ```

2. **Send Email Notification**
   ```python
   from claims.tasks import send_email_notification
   send_email_notification.delay(
       subject='Test Email',
       message='Hello World',
       recipient_list=['user@example.com']
   )
   ```

3. **Process Batch Import**
   ```python
   from claims.tasks import process_batch_import
   process_batch_import.delay(
       file_path='/path/to/import.xlsx',
       user_id=user.id
   )
   ```

### Monitoring Celery

```bash
# View active tasks
celery -A claims_system inspect active

# View registered tasks
celery -A claims_system inspect registered

# View task statistics
celery -A claims_system inspect stats

# Flower - Web-based monitoring (optional)
pip install flower
celery -A claims_system flower
# Access at http://localhost:5555
```

### Production Deployment

For production, use a process manager like Supervisor:

```ini
# /etc/supervisor/conf.d/celery.conf
[program:celery_worker]
command=/path/to/venv/bin/celery -A claims_system worker -l info
directory=/path/to/claims-management-system
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_error.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A claims_system beat -l info
directory=/path/to/claims-management-system
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_error.log
```

---

## Caching Strategy

### Redis Cache Configuration

The system uses Redis for caching in production to improve performance.

### Cache Timeouts

```python
from django.conf import settings

CACHE_TTL = {
    'short': 60,     # 1 minute
    'medium': 300,   # 5 minutes
    'long': 3600,    # 1 hour
    'day': 86400,    # 24 hours
}
```

### Using Cache

```python
from django.core.cache import cache

# Set cache
cache.set('key', 'value', timeout=300)  # 5 minutes

# Get cache
value = cache.get('key')

# Delete cache
cache.delete('key')

# Clear all cache
cache.clear()
```

### Cache Decorators

```python
from django.views.decorators.cache import cache_page

# Cache view for 5 minutes
@cache_page(60 * 5)
def my_view(request):
    ...
```

### Caching Best Practices

1. **Cache Analytics Queries** - Cache expensive database queries
2. **Cache User Permissions** - Cache role-based permissions
3. **Cache Export Results** - Cache generated reports
4. **Invalidate on Updates** - Clear cache when data changes

---

## Security Features

### Implemented Security Measures

✅ **Environment Variables** - Sensitive data externalized
✅ **SSL/HTTPS Configuration** - Secure connections
✅ **Session Security** - HTTP-only, SameSite cookies
✅ **CSRF Protection** - Anti cross-site request forgery
✅ **Security Headers** - CSP, X-Frame-Options, etc.
✅ **File Upload Validation** - Size, extension, MIME type checks
✅ **Rate Limiting** - Login and export rate limits
✅ **Structured Logging** - Comprehensive audit trail
✅ **SQL Injection Protection** - Django ORM parameterization
✅ **XSS Prevention** - Template auto-escaping

### Security Tests

Run security-focused tests:

```bash
# Run all security tests
pytest -m security

# Run specific security test classes
pytest claims/test_security.py::TestSQLInjection
pytest claims/test_security.py::TestXSSPrevention
pytest claims/test_security.py::TestCSRFProtection
```

### Security Scanning

```bash
# Install security tools
pip install bandit safety

# Run bandit (security linter)
bandit -r claims ships port_activities

# Check for vulnerable dependencies
safety check

# Generate security report
bandit -r claims ships port_activities -f json -o security-report.json
```

### Security Checklist for Production

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY` (50+ random characters)
- [ ] Enable `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use HTTPS for all connections
- [ ] Enable Redis for rate limiting
- [ ] Set up firewall rules
- [ ] Regular security audits with bandit/safety
- [ ] Keep dependencies updated
- [ ] Enable two-factor authentication (future)

---

## Code Quality Tools

### Pre-commit Hooks

Install and configure pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Code Formatting

```bash
# Format with black
black --line-length=120 .

# Check formatting (no changes)
black --check --line-length=120 .

# Format specific file
black claims/models.py
```

### Linting

```bash
# Run flake8
flake8 .

# Run with specific rules
flake8 --max-line-length=120 --extend-ignore=E203,E266,E501 .

# Check specific file
flake8 claims/models.py
```

### Type Checking

```bash
# Run mypy
mypy claims ships port_activities

# Generate type coverage report
mypy --html-report mypy-report claims ships port_activities
```

### Import Sorting

```bash
# Sort imports with isort
isort --profile black --line-length 120 .

# Check only (no changes)
isort --check --profile black --line-length 120 .
```

---

## Environment Variables Reference

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-50-characters-minimum
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=claims_db
DB_USER=claims_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_AGE=3600

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# RADAR Integration
RADAR_API_URL=https://radar-api.example.com
RADAR_API_KEY=your-radar-api-key
RADAR_SYNC_RETRY_ATTEMPTS=3
RADAR_SYNC_RETRY_DELAY=5

# File Uploads
MAX_UPLOAD_SIZE=10485760
ALLOWED_UPLOAD_EXTENSIONS=pdf,docx,xlsx,jpg,jpeg,png,txt

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATELIMIT_ENABLE=True
```

---

## Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your settings

# 3. Run migrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Collect static files (production)
python manage.py collectstatic

# 6. Start Redis (separate terminal)
redis-server

# 7. Start Celery worker (separate terminal)
celery -A claims_system worker -l info

# 8. Start Celery beat (separate terminal)
celery -A claims_system beat -l info

# 9. Run development server
python manage.py runserver

# 10. Run tests
pytest
```

---

## Troubleshooting

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Test connection
redis-cli
> set test "hello"
> get test
> quit
```

### Celery Not Processing Tasks

```bash
# Check worker is running
celery -A claims_system inspect active

# Restart worker
# Ctrl+C to stop, then restart:
celery -A claims_system worker -l info

# Check for errors in logs
tail -f logs/django.log
```

### Cache Issues

```bash
# Clear Django cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()

# Clear Redis cache
redis-cli
> FLUSHDB
> quit
```

### Test Failures

```bash
# Run with verbose output
pytest -v --tb=short

# Run specific failing test
pytest path/to/test.py::TestClass::test_method -v

# Check test database
python manage.py test --debug-mode
```

---

## Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Celery Documentation**: https://docs.celeryproject.org/
- **pytest Documentation**: https://docs.pytest.org/
- **Redis Documentation**: https://redis.io/documentation
- **GitHub Actions**: https://docs.github.com/en/actions

---

*Last Updated: January 3, 2026*

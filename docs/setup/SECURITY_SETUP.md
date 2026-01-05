# Security Setup Guide

This guide covers the security improvements implemented in the Claims Management System.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Security Settings](#security-settings)
3. [File Upload Security](#file-upload-security)
4. [Rate Limiting](#rate-limiting)
5. [Logging](#logging)
6. [Production Deployment](#production-deployment)

## Environment Variables

### Initial Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate a new SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Update .env with your configuration:**
   ```ini
   SECRET_KEY=your-newly-generated-secret-key
   DEBUG=True  # Set to False in production
   ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
   ```

### Required Environment Variables

- `SECRET_KEY`: Django secret key (required for production)
- `DEBUG`: Enable/disable debug mode (default: False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

### Optional Environment Variables

See [.env.example](.env.example) for a complete list of optional configuration options.

## Security Settings

### HTTPS/SSL Configuration (Production)

Update your `.env` file:

```ini
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Session Security

Sessions are configured to:
- Expire after 1 hour of inactivity (configurable)
- Use HTTP-only cookies (prevents XSS attacks)
- Use Lax SameSite policy (prevents CSRF attacks)
- Save on every request to update timeout

Configure in `.env`:
```ini
SESSION_COOKIE_AGE=3600  # 1 hour in seconds
SESSION_SAVE_EVERY_REQUEST=True
```

### Security Headers

The following security headers are automatically added to all responses:

- **Content-Security-Policy**: Prevents XSS attacks
- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-Frame-Options**: Prevents clickjacking (set to DENY)
- **Referrer-Policy**: Controls referrer information
- **Permissions-Policy**: Restricts browser features

## File Upload Security

### Configuration

Set file upload limits in `.env`:

```ini
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
ALLOWED_UPLOAD_EXTENSIONS=pdf,docx,xlsx,jpg,jpeg,png,txt
```

### Security Features

1. **File Size Validation**: Files exceeding `MAX_UPLOAD_SIZE` are rejected
2. **Extension Validation**: Only allowed file extensions are accepted
3. **MIME Type Validation**: File content type is verified
4. **Filename Sanitization**: Filenames are cleaned to prevent path traversal
5. **Security Scanning**: Files are checked for malicious patterns

### Middleware

The `FileUploadValidationMiddleware` automatically validates all file uploads:

- Checks file size before processing
- Validates file extension against whitelist
- Verifies MIME type matches expected content
- Sanitizes filenames
- Logs all upload attempts and rejections

## Rate Limiting

### Configuration

Enable rate limiting in `.env`:

```ini
RATELIMIT_ENABLE=True
LOGIN_RATE_LIMIT=5/5m  # 5 attempts per 5 minutes
EXPORT_RATE_LIMIT=10/h  # 10 exports per hour
```

### Protected Endpoints

Rate limiting is automatically applied to:

1. **Login Attempts**: Prevents brute force attacks
   - Default: 5 attempts per 5 minutes per IP
   - After limit: 429 error page

2. **Export Endpoints**: Prevents resource exhaustion
   - Default: 10 exports per hour per user
   - After limit: 429 error page

### Using Rate Limiting in Views

#### For Login Views:

```python
from claims_system.decorators import login_rate_limit

@login_rate_limit
def login_view(request):
    # Your login logic
    pass
```

#### For Export Views:

```python
from claims_system.decorators import export_rate_limit

@export_rate_limit
def export_claims_view(request):
    # Your export logic
    pass
```

#### Custom Rate Limits:

```python
from claims_system.decorators import api_rate_limit

@api_rate_limit('50/h')
def custom_api_view(request):
    # Your API logic
    pass
```

## Logging

### Configuration

Logs are automatically created in the `logs/` directory:

- `django.log`: General application logs
- `errors.log`: Error-level logs (JSON format)
- `security.log`: Security-related events (JSON format)

Configure log level in `.env`:

```ini
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Rotation

Logs are automatically rotated:
- Maximum size: 10MB per file
- Backup count: 5 files (10 for security logs)
- Format: Rotating file handler

### What Gets Logged

1. **General Logs** (`django.log`):
   - Request/response cycles
   - Database queries (in DEBUG mode)
   - Application events

2. **Error Logs** (`errors.log`):
   - Exceptions and errors
   - Stack traces
   - Request context

3. **Security Logs** (`security.log`):
   - Failed login attempts
   - File upload rejections
   - Rate limit violations
   - Permission denied events

### Using Logging in Code

```python
import logging

logger = logging.getLogger(__name__)

# Info level
logger.info("Voyage assigned successfully", extra={'voyage_id': voyage.id})

# Warning level
logger.warning("File upload rejected", extra={'filename': file.name, 'reason': 'size'})

# Error level
logger.error("RADAR sync failed", exc_info=True, extra={'voyage_id': voyage.id})
```

## Retry Logic for RADAR Sync

### Configuration

Set retry parameters in `.env`:

```ini
RADAR_SYNC_RETRY_ATTEMPTS=3
RADAR_SYNC_RETRY_DELAY=5  # seconds
```

### Using Retry Decorator

```python
from claims_system.utils import retry_on_failure

@retry_on_failure(max_attempts=3, delay=5, exponential_backoff=True)
def sync_voyage_with_radar(voyage_id):
    # Your RADAR sync logic
    # Will automatically retry on failure
    pass
```

### Features

- Configurable retry attempts
- Configurable delay between retries
- Optional exponential backoff
- Automatic logging of retry attempts
- Raises exception after max attempts

## Production Deployment

### Pre-Deployment Checklist

- [ ] Generate and set a new `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain(s)
- [ ] Enable SSL/HTTPS settings
- [ ] Set up database (PostgreSQL or SQL Server)
- [ ] Configure email backend
- [ ] Set up file storage (Azure Blob or SharePoint)
- [ ] Review and configure rate limits
- [ ] Set appropriate `SESSION_COOKIE_AGE`
- [ ] Configure logging directory with proper permissions
- [ ] Set up log rotation in production
- [ ] Test all security features
- [ ] Run security audit

### Environment-Specific Settings

#### Development (.env)
```ini
DEBUG=True
SECRET_KEY=development-key
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.sqlite3
```

#### Production (.env.production)
```ini
DEBUG=False
SECRET_KEY=production-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=claims_db
DB_USER=claims_user
DB_PASSWORD=secure-password
DB_HOST=db.example.com
DB_PORT=5432
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

### Security Audit Commands

```bash
# Check for security issues
python manage.py check --deploy

# Run tests with coverage
pytest

# Check code quality
flake8 .
black --check .
mypy .

# Test file upload security
# (Manual testing required)

# Verify rate limiting
# (Manual testing required)
```

### Monitoring

Monitor the following in production:

1. **Security Logs**: Watch for suspicious activity
2. **Error Logs**: Track application errors
3. **Rate Limit Violations**: Identify potential attacks
4. **File Upload Attempts**: Monitor for malicious uploads
5. **Failed Login Attempts**: Track brute force attempts

### Additional Security Measures

Consider implementing:

1. **Web Application Firewall (WAF)**
2. **Intrusion Detection System (IDS)**
3. **Regular security audits**
4. **Penetration testing**
5. **Dependency vulnerability scanning**
6. **Database encryption at rest**
7. **Network security groups**
8. **DDoS protection**

## Support

For security issues or questions, contact your system administrator.

**Never commit the `.env` file to version control!**

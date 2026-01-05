# Testing Guide

## Overview

This guide covers the comprehensive testing and error handling system in the Claims Management System.

**Current Status**: ✅ **292 tests** (290 passing) | **44.69% Coverage** (Target: 70%)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Suite Status](#test-suite-status)
3. [Running Tests](#running-tests)
4. [Test Infrastructure](#test-infrastructure)
5. [Error Handling & Protection](#error-handling--protection)
6. [Writing Tests](#writing-tests)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific app tests
pytest ships/tests.py
pytest port_activities/tests.py
pytest claims/tests.py

# Run verbose
pytest -v
```

---

## Test Suite Status

### Test Files Overview

**Total: 8 test files with 292 tests**

#### Claims App Tests

1. **[claims/tests.py](../../claims/tests.py)** - Core models (enhanced)
   - User Model (29 tests)
   - ShipOwner Model (10 tests)
   - Voyage Model (17 tests)
   - Claim Model (23 tests)
   - VoyageAssignment Model (4 tests)
   - ClaimActivityLog Model (4 tests)

2. **[claims/test_security.py](../../claims/test_security.py)** - Security tests (enhanced)
   - SQL injection prevention
   - XSS prevention
   - CSRF protection
   - Authentication & authorization
   - Session security

3. **[claims/test_views.py](../../claims/test_views.py)** - View tests (60 tests)
   - Dashboard, voyages, claims, users
   - Authentication, analytics, exports

4. **[claims/test_views_extended.py](../../claims/test_views_extended.py)** - Extended views (32 tests)
   - Status updates, assignments, comments
   - Documents, filtering, permissions

5. **[claims/test_api_views.py](../../claims/test_api_views.py)** - REST API (24 tests)
   - Claim/Voyage/ShipOwner/User APIs
   - Filtering, pagination, permissions

6. **[claims/test_services.py](../../claims/test_services.py)** - Services (22 tests)
   - Excel export service
   - Notification service
   - RADAR sync service

#### Ships App Tests

7. **[ships/tests.py](../../ships/tests.py)** - Models (38 tests)
   - Ship, TCFleet, ShipSpecification models
   - Business logic and validations

8. **[ships/test_views.py](../../ships/test_views.py)** - Views (18 tests)
   - Ship management views
   - Fleet management, exports

#### Port Activities App Tests

9. **[port_activities/tests.py](../../port_activities/tests.py)** - Models (44 tests)
   - ActivityType, PortActivity models
   - Duration calculations, RADAR sync

10. **[port_activities/test_views.py](../../port_activities/test_views.py)** - Views (17 tests)
    - Port activity management views
    - Activity type management, exports

**Result**: ✅ 290 passing, 2 failing (99.3% pass rate)

---

## Test Statistics

| App | Tests | Status | Coverage % |
|-----|-------|--------|-----------|
| **claims** (models) | 89% | ✅ Excellent | Models, Serializers, Forms |
| **claims** (views) | 51% | ⚠️ Moderate | Views (target: 80%) |
| **claims** (api_views) | 67% | ⚠️ Moderate | API endpoints |
| **claims** (services) | 23-37% | ⚠️ Low | Services (target: 60%) |
| **ships** (models) | 94% | ✅ Excellent | Ship models |
| **ships** (views) | 7% | 🔴 Low | Views (HIGH PRIORITY) |
| **port_activities** (models) | 100% | ✅ Perfect | Port activity models |
| **port_activities** (views) | 20% | 🔴 Low | Views (HIGH PRIORITY) |
| **system** (celery) | 92% | ✅ Excellent | Background tasks |
| **Total** | **292 tests** | **290 passing** | **44.69%** (Target: 70%) |

For detailed coverage breakdown, see [TEST_COVERAGE_REPORT.md](TEST_COVERAGE_REPORT.md)

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific app
pytest ships/tests.py
pytest port_activities/tests.py
pytest claims/tests.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov
pytest --cov-report=html  # Generate HTML report
```

### Django Test Runner

```bash
# Run all tests
./venv/Scripts/python manage.py test

# Run specific test class
./venv/Scripts/python manage.py test claims.tests.ConcurrencyTestCase

# Run with verbosity
./venv/Scripts/python manage.py test -v 2
```

### Test Markers

```bash
# Run specific test types
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m security       # Security tests only
pytest -m slow           # Slow-running tests
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=claims --cov=ships --cov=port_activities --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=claims --cov=ships --cov=port_activities --cov-report=html

# View report (open htmlcov/index.html)

# Coverage target: 70% (currently 44.69%)
```

---

## Test Infrastructure

### Testing Tools

✅ **pytest** - Modern testing framework
- Configuration: [pytest.ini](../../pytest.ini)
- Django integration via pytest-django
- Fixtures for test data
- Markers for test categorization

✅ **Coverage Reporting**
- Configuration: [.coveragerc](../../.coveragerc)
- HTML, terminal, and XML reports
- Target: 70% minimum coverage
- Excludes: migrations, tests, settings

✅ **Code Quality Tools**
- **flake8**: Linting
- **black**: Code formatting
- **mypy**: Type checking
- Configuration: [setup.cfg](../../setup.cfg)

### Test Markers

```python
@pytest.mark.unit         # Unit tests
@pytest.mark.integration  # Integration tests
@pytest.mark.security     # Security tests
@pytest.mark.slow         # Slow-running tests
```

---

## Error Handling & Protection

The system protects against:
1. **Concurrent editing conflicts** - Multiple users editing same record
2. **Database failures** - Connection errors, timeouts, server issues
3. **Data integrity issues** - Invalid data and constraint violations

### Concurrency Protection (Optimistic Locking)

**Problem**:
- User A edits Claim #123, saves changes
- User B edits Claim #123 simultaneously
- Without protection: User B overwrites User A's work

**Solution**: Version field on each record

```python
class Claim(models.Model):
    version = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.pk:
            current = Claim.objects.filter(pk=self.pk).values('version').first()
            if current and current['version'] != self.version:
                raise ValidationError("Record modified by another user")
            self.version += 1
        super().save(*args, **kwargs)
```

**User Experience**:
- User B gets friendly error message
- Clear explanation of conflict
- Instructions to reload and reapply changes

### Database Error Handling

**Errors Handled**:
1. **Connection Refused** - Database server down
2. **Query Timeout** - Complex query takes too long
3. **Duplicate Data** - Unique constraint violation
4. **Data Validation** - Foreign key or integrity errors

**Implementation**: Middleware intercepts exceptions

**File**: [claims/middleware.py](../../claims/middleware.py)

```python
MIDDLEWARE = [
    'claims.middleware.DatabaseErrorHandlingMiddleware',
    'claims.middleware.ConcurrencyWarningMiddleware',
]
```

### User-Friendly Error Pages

All error pages include:
- Clear, non-technical explanation
- Impact statement (what user cannot do)
- Action list (3-5 concrete steps)
- Quick action buttons
- Error code for IT support
- Technical details (admin only)

**Error Templates**:
| Template | Purpose | Error Code |
|----------|---------|------------|
| database_connection.html | Database unreachable | DB-CONN-503 |
| database_timeout.html | Query too slow | DB-TIMEOUT-504 |
| concurrent_edit.html | Version conflict | CONCURRENT-EDIT-409 |
| duplicate_data.html | Unique constraint | DUP-DATA-400 |
| data_validation.html | Invalid data | DATA-VAL-400 |

---

## Writing Tests

### Test Organization

```python
import pytest
from django.test import TransactionTestCase

@pytest.mark.django_db
class TestModelName:
    """Test ModelName functionality"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_model_creation(self, test_user):
        """Test basic model creation"""
        obj = ModelName.objects.create(...)
        assert obj.pk is not None

    def test_model_validation(self):
        """Test model validation rules"""
        with pytest.raises(ValidationError):
            ModelName.objects.create(invalid_data=...)
```

### Test Naming Conventions

✅ **Good**:
- `test_is_charter_active_when_dates_valid`
- `test_claim_amount_cannot_be_negative`
- `test_concurrent_claim_updates_raise_conflict`

❌ **Bad**:
- `test_1`
- `test_function`
- `test_it_works`

### Test Coverage Focus

1. **Model Functionality**
   - Creation and validation
   - Properties and computed fields
   - Business logic methods
   - Uniqueness constraints

2. **Integration**
   - Cross-app relationships
   - Foreign key behavior (PROTECT, SET_NULL, CASCADE)
   - Reverse relations

3. **Edge Cases**
   - Boundary values
   - Empty/null values
   - Invalid data
   - Overlapping/conflicting data

4. **Business Rules**
   - Status transitions
   - Calculations
   - Validation rules
   - Permissions

### Fixtures for Test Data

```python
@pytest.fixture
def ship_owner():
    return ShipOwner.objects.create(name="Test Owner")

@pytest.fixture
def test_ship(ship_owner):
    return Ship.objects.create(
        name="Test Ship",
        imo_number="1234567",
        owner=ship_owner
    )

@pytest.fixture
def test_voyage(test_ship):
    return Voyage.objects.create(
        ship=test_ship,
        voyage_number="V001"
    )
```

---

## Test Classes Reference

### ConcurrencyTestCase

**Purpose**: Test concurrent editing scenarios

**Tests**:
- `test_concurrent_claim_updates()` - Two users editing same claim
- `test_concurrent_voyage_assignment()` - Two users assigning same voyage

**Run**:
```bash
pytest claims/tests.py::ConcurrencyTestCase -v
```

### DatabaseErrorTestCase

**Purpose**: Test database failure scenarios

**Tests**:
- `test_database_connection_error_on_voyage_list()`
- `test_database_timeout_on_claim_detail()`
- `test_radar_sync_connection_failure()`

**Run**:
```bash
pytest claims/tests.py::DatabaseErrorTestCase -v
```

### DataIntegrityTestCase

**Purpose**: Test data validation

**Tests**:
- `test_claim_amount_cannot_be_negative()`
- `test_paid_amount_cannot_exceed_claim_amount()`

**Run**:
```bash
pytest claims/tests.py::DataIntegrityTestCase -v
```

---

## Troubleshooting

### Tests Fail with "DatabaseError"

**Cause**: Database not configured for tests

**Solution**:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'TEST': {
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }
}
```

### Concurrent Tests Don't Work

**Cause**: Need `TransactionTestCase` not `TestCase`

**Solution**:
```python
from django.test import TransactionTestCase

class ConcurrencyTestCase(TransactionTestCase):  # Not TestCase
    ...
```

### Error Pages Don't Show

**Cause**: Middleware not enabled or DEBUG=True

**Solution**:
```python
# settings.py
DEBUG = False  # Error pages only show when DEBUG=False
ALLOWED_HOSTS = ['*']

MIDDLEWARE = [
    ...
    'claims.middleware.DatabaseErrorHandlingMiddleware',
]
```

### Version Field Missing

**Cause**: Migration not run

**Solution**:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Best Practices

### For Developers

1. **Always Test Error Scenarios**
   - Don't just test the "happy path"
   - Test what happens when things go wrong
   - Test edge cases

2. **Write User-Friendly Messages**
   - Avoid technical jargon
   - Explain what happened in simple terms
   - Tell users what to do next

3. **Use Optimistic Locking for Edits**
   - Include version field in forms
   - Check version before saving
   - Show clear error on conflict

4. **Log All Errors**
   - Use Python logging module
   - Include context (user, request path)
   - Log to file for debugging

### For Users

1. **If You See a Conflict Error**:
   - Copy your changes to notepad
   - Refresh to see latest data
   - Reapply changes if needed
   - Coordinate with team

2. **If Database is Down**:
   - Wait and try again
   - Check with colleagues
   - Contact IT support
   - Save work elsewhere

3. **Preventing Conflicts**:
   - Communicate before editing shared records
   - Add comment that you're working on it
   - Save changes quickly
   - Don't leave edit pages open long

---

## Testing Checklist

Before deploying:

- [ ] Run all tests: `pytest`
- [ ] Check test coverage: >= 70%
- [ ] Test error pages with DEBUG=False
- [ ] Test concurrent editing with 2 browsers
- [ ] Simulate database failure
- [ ] Verify error codes display
- [ ] Check logs for error details
- [ ] Ensure technical details only show to admins
- [ ] Test different user roles

---

## Next Steps to 70% Coverage

### High Priority (High Impact)

1. **Complete View Coverage** (+15% potential)
   - Improve claims/views.py: 51% → 80%
   - Improve ships/views.py: 7% → 60%
   - Improve port_activities/views.py: 20% → 60%

2. **Improve Service Tests** (+8% potential)
   - Add implementation tests for services
   - Mock external dependencies properly
   - Test error handling and edge cases

3. **Middleware Testing** (+3% potential)
   - Test authentication middleware
   - Test password change enforcement
   - Test timezone handling

### Estimated Effort
- View tests: ~100 additional test cases
- Service tests: ~30 additional test cases
- Middleware tests: ~20 additional test cases
- Integration tests: ~15 additional test cases
- **Total**: ~165 additional test cases to reach 70%

For detailed roadmap, see [TEST_COVERAGE_REPORT.md](TEST_COVERAGE_REPORT.md)

---

## Coverage Goals

**Target**: 70%+ per app

Current configuration fails build if coverage < 70%:

```ini
# pytest.ini
--cov-fail-under=70
```

**Generate HTML Report**:
```bash
pytest --cov-report=html
# Open htmlcov/index.html
```

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/5.2/topics/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

*Last Updated: January 5, 2026*

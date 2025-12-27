# Testing & Error Handling Documentation

## Overview

This document explains the comprehensive testing and error handling system implemented in the Claims Management System. The system protects against:

1. **Concurrent editing conflicts** - Multiple users editing the same record
2. **Database failures** - Connection errors, timeouts, and server issues
3. **Data integrity issues** - Invalid data and constraint violations

---

## Table of Contents

1. [Running Tests](#running-tests)
2. [Concurrency Protection](#concurrency-protection)
3. [Database Error Handling](#database-error-handling)
4. [User-Friendly Error Messages](#user-friendly-error-messages)
5. [Test Coverage](#test-coverage)
6. [Troubleshooting](#troubleshooting)

---

## Running Tests

### Run All Tests
```bash
./venv/Scripts/python manage.py test claims.tests
```

### Run Specific Test Class
```bash
# Concurrency tests only
./venv/Scripts/python manage.py test claims.tests.ConcurrencyTestCase

# Database error tests
./venv/Scripts/python manage.py test claims.tests.DatabaseErrorTestCase

# Data integrity tests
./venv/Scripts/python manage.py test claims.tests.DataIntegrityTestCase
```

### Run with Verbosity
```bash
# Detailed output
./venv/Scripts/python manage.py test claims.tests -v 2

# Very detailed output
./venv/Scripts/python manage.py test claims.tests -v 3
```

### Run with Coverage Report
```bash
# Install coverage first
./venv/Scripts/pip install coverage

# Run tests with coverage
./venv/Scripts/coverage run --source='claims' manage.py test claims.tests
./venv/Scripts/coverage report
./venv/Scripts/coverage html  # Generate HTML report
```

---

## Concurrency Protection

### Problem: Simultaneous Edits

**Scenario**:
- User A opens Claim #123 at 10:00 AM
- User B opens Claim #123 at 10:01 AM
- User A updates the amount to $50,000 and saves at 10:02 AM
- User B updates the amount to $60,000 and tries to save at 10:03 AM

**Without Protection**:
- User B's changes would overwrite User A's changes
- User A's work is lost without warning

**With Optimistic Locking**:
- User B gets a clear error message
- System explains someone else modified the record
- User B can reload and see User A's changes
- User B can then make informed decision about their edits

### How It Works

#### 1. Version Field
Every Claim has a `version` field that increments on each save:

```python
class Claim(models.Model):
    version = models.IntegerField(default=0, help_text="Version number for optimistic locking")
```

#### 2. Version Check on Save
Before saving, the system checks if the version matches:

```python
def save(self, *args, **kwargs):
    if self.pk is not None:  # Existing record
        current = Claim.objects.filter(pk=self.pk).values('version').first()
        if current and current['version'] != self.version:
            raise ValidationError(
                "This claim has been modified by another user. "
                "Please reload the page and try again."
            )
        self.version += 1  # Increment for next save
    super().save(*args, **kwargs)
```

#### 3. User-Friendly Error Page
When conflict detected, user sees: [concurrent_edit.html](claims/templates/errors/concurrent_edit.html)

**What the user sees**:
- Clear explanation of what happened
- Visual timeline of events
- Step-by-step instructions on what to do
- Tips to prevent future conflicts
- Error code for IT support

### Testing Concurrency

**Test**: `test_concurrent_claim_updates()`

This test:
1. Creates two test users
2. Both load the same claim
3. User 1 updates and saves
4. User 2 tries to update
5. Verifies User 2 gets conflict error

**Run this test**:
```bash
./venv/Scripts/python manage.py test claims.tests.ConcurrencyTestCase.test_concurrent_claim_updates
```

---

## Database Error Handling

### Errors Handled

#### 1. Connection Refused / Database Down

**When**: Database server is offline or unreachable

**User Sees**:
- **Error Type**: "Database Connection Error"
- **Message**: "The database server is currently unavailable"
- **Impact**: "You cannot view or update any data until connection is restored"
- **Actions**:
  - Wait and refresh
  - Contact IT support
  - Check with other users
- **Error Code**: DB-CONN-503

**Example**:
```
Database: PostgreSQL at 192.168.1.100
Status: Connection refused (server down)
User Action: Tries to view voyage list
Result: Shows database_connection.html
```

#### 2. Query Timeout

**When**: Query takes too long (complex query, high server load)

**User Sees**:
- **Error Type**: "Database Timeout"
- **Message**: "The database query took too long to complete"
- **Impact**: "The page could not be loaded in time"
- **Actions**:
  - Refresh the page
  - Simplify filters
  - Try during off-peak hours
- **Error Code**: DB-TIMEOUT-504

#### 3. Duplicate Data / Unique Constraint

**When**: Trying to create duplicate record (e.g., same claim number)

**User Sees**:
- **Error Type**: "Duplicate Data"
- **Message**: "This record already exists"
- **Impact**: "Your changes were not saved"
- **Actions**:
  - Check if record exists
  - Modify data to make it unique
  - Contact support

#### 4. Data Validation / Integrity Error

**When**: Data violates database rules (e.g., foreign key constraint)

**User Sees**:
- **Error Type**: "Data Validation Error"
- **Message**: "Invalid data was provided"
- **Impact**: "Your changes were not saved"
- **Actions**:
  - Review data entered
  - Ensure required fields filled
  - Contact support if needed

### Middleware Implementation

The [DatabaseErrorHandlingMiddleware](claims/middleware.py) intercepts exceptions and shows user-friendly pages instead of technical stack traces.

**Enabled in settings.py**:
```python
MIDDLEWARE = [
    # ... other middleware ...
    'claims.middleware.DatabaseErrorHandlingMiddleware',
    'claims.middleware.ConcurrencyWarningMiddleware',
]
```

### Testing Database Errors

**Tests Available**:
1. `test_database_connection_error_on_voyage_list()` - Simulates connection failure
2. `test_database_timeout_on_claim_detail()` - Simulates timeout
3. `test_radar_sync_connection_failure()` - Placeholder for RADAR integration

**Run database error tests**:
```bash
./venv/Scripts/python manage.py test claims.tests.DatabaseErrorTestCase
```

---

## User-Friendly Error Messages

### Design Principles

All error pages follow these principles:

1. **Clear, Non-Technical Language**
   - ❌ "OperationalError: could not connect to server"
   - ✅ "The database server is currently unavailable"

2. **Explain Impact**
   - Tell user what they can/cannot do
   - Be specific about what was affected

3. **Provide Actions**
   - Give 3-5 concrete steps
   - Order by likelihood of success
   - Include support contact

4. **Use Visual Hierarchy**
   - Color-coded severity (danger=red, warning=yellow, info=blue)
   - Icons for quick recognition
   - Collapsible technical details for admins

5. **Include Error Codes**
   - Helps IT support diagnose issues
   - Users can reference when calling support

### Error Page Structure

All error pages include:

```html
<div class="card border-{severity}">
    <div class="card-header bg-{severity}">
        <h4><i class="bi bi-icon"></i> {Error Type}</h4>
    </div>
    <div class="card-body">
        <!-- User-friendly alert -->
        <div class="alert alert-{severity}">
            <h5>{Error Message}</h5>
            <p>{User Message}</p>
        </div>

        <!-- Impact statement -->
        <div>
            <strong>Impact:</strong> {What the user cannot do}
        </div>

        <!-- Action list -->
        <div>
            <strong>What to do:</strong>
            <ul>
                <li>{Step 1}</li>
                <li>{Step 2}</li>
                <li>{Step 3}</li>
            </ul>
        </div>

        <!-- Quick action buttons -->
        <div>
            <button>Try Again</button>
            <a href="dashboard">Dashboard</a>
        </div>

        <!-- Technical details (admin only) -->
        {% if user.is_staff %}
        <details>
            <summary>Technical Details</summary>
            <pre>{Exception details}</pre>
        </details>
        {% endif %}

        <!-- Error code -->
        <p><small>Error code: {CODE}</small></p>
    </div>
</div>
```

### Error Templates Created

| File | Purpose | When Shown |
|------|---------|------------|
| [database_connection.html](claims/templates/errors/database_connection.html) | Database unreachable | Connection refused, network down |
| [database_timeout.html](claims/templates/errors/database_timeout.html) | Query too slow | Timeout, complex query |
| [database_error.html](claims/templates/errors/database_error.html) | Generic DB error | Other database issues |
| [concurrent_edit.html](claims/templates/errors/concurrent_edit.html) | Multiple users editing same record | Version conflict |
| [duplicate_data.html](claims/templates/errors/duplicate_data.html) | Unique constraint violated | Duplicate claim number, etc. |
| [data_validation.html](claims/templates/errors/data_validation.html) | Invalid data | Foreign key violation, etc. |

---

## Test Coverage

### Test Classes

#### 1. ConcurrencyTestCase
**Purpose**: Test concurrent editing scenarios

**Tests**:
- `test_concurrent_claim_updates()` - Two users editing same claim
- `test_concurrent_voyage_assignment()` - Two users assigning same voyage

**What it tests**:
- Optimistic locking works
- Version conflicts detected
- Only one modification succeeds
- Clear error messages shown

#### 2. DatabaseErrorTestCase
**Purpose**: Test database failure scenarios

**Tests**:
- `test_database_connection_error_on_voyage_list()` - Connection failure
- `test_database_timeout_on_claim_detail()` - Query timeout
- `test_radar_sync_connection_failure()` - External system failure

**What it tests**:
- Errors caught gracefully
- User sees friendly message
- No technical stack traces
- Appropriate HTTP status codes

#### 3. ErrorMessageTestCase
**Purpose**: Test error message clarity

**Tests**:
- `test_permission_denied_clear_message()` - Permission errors
- `test_missing_required_field_clear_message()` - Form validation
- `test_voyage_already_assigned_clear_message()` - Business logic errors

**What it tests**:
- Messages are user-friendly
- Actions are clear
- No jargon used

#### 4. DataIntegrityTestCase
**Purpose**: Test data validation

**Tests**:
- `test_claim_amount_cannot_be_negative()` - Negative amounts rejected
- `test_paid_amount_cannot_exceed_claim_amount()` - Overpayment warning

**What it tests**:
- Invalid data rejected
- Database constraints enforced
- Validation errors raised

#### 5. PerformanceTestCase
**Purpose**: Test query performance

**Tests**:
- `test_voyage_list_query_count()` - N+1 query detection

**What it tests**:
- Pages don't make excessive queries
- select_related() and prefetch_related() used correctly

### Test Data

Tests automatically create:
- Users (admin, analysts)
- Ship owners
- Voyages
- Claims
- Comments

All test data is isolated and cleaned up after tests.

---

## Troubleshooting

### Common Issues

#### 1. Tests Fail with "DatabaseError"

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

#### 2. Concurrent Tests Don't Work

**Cause**: Tests need `TransactionTestCase` not `TestCase`

**Solution**: Use `TransactionTestCase` for concurrency tests:
```python
class ConcurrencyTestCase(TransactionTestCase):  # Not TestCase
    ...
```

#### 3. Error Pages Don't Show

**Cause**: Middleware not enabled or DEBUG=True

**Solution**:
```python
# settings.py
DEBUG = False  # Error pages only show when DEBUG=False
ALLOWED_HOSTS = ['*']  # Or specific hosts

MIDDLEWARE = [
    ...
    'claims.middleware.DatabaseErrorHandlingMiddleware',
]
```

#### 4. Version Field Missing

**Cause**: Migration not run

**Solution**:
```bash
./venv/Scripts/python manage.py makemigrations
./venv/Scripts/python manage.py migrate
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
   - Include context (user, request path, etc.)
   - Log to file for production debugging

### For Users

1. **If You See a Conflict Error**:
   - Don't panic - your work is protected
   - Copy your changes to notepad first
   - Refresh the page to see latest data
   - Reapply your changes if still needed
   - Coordinate with team to avoid conflicts

2. **If Database is Down**:
   - Wait a few minutes and try again
   - Check with colleagues
   - Contact IT support
   - Save your work elsewhere

3. **Preventing Conflicts**:
   - Communicate with team before editing shared records
   - Add a comment saying you're working on it
   - Save changes quickly
   - Don't leave edit pages open for long periods

---

## Testing Checklist

Before deploying:

- [ ] Run all tests: `python manage.py test`
- [ ] Check test coverage: > 80%
- [ ] Test error pages with DEBUG=False
- [ ] Test concurrent editing with 2 browsers
- [ ] Simulate database failure (stop database server)
- [ ] Verify error codes show correctly
- [ ] Check logs for error details
- [ ] Ensure technical details only show to admins
- [ ] Test on different screen sizes
- [ ] Test with different user roles

---

## Error Code Reference

| Code | Meaning | User Action |
|------|---------|-------------|
| DB-CONN-503 | Database connection failed | Wait and retry, contact IT |
| DB-TIMEOUT-504 | Database query timeout | Simplify search, try later |
| CONCURRENT-EDIT-409 | Version conflict | Reload page, reapply changes |
| DUP-DATA-400 | Duplicate record | Check existing data |
| DATA-VAL-400 | Invalid data | Review form, fix errors |

---

## Future Enhancements

Potential improvements:

1. **Real-Time Conflict Detection**
   - Show warning if another user is viewing same record
   - Use WebSockets to notify users
   - Lock records for short periods

2. **Audit Trail**
   - Log all changes with version numbers
   - Show who changed what and when
   - Allow reverting to previous versions

3. **Automatic Retry**
   - Retry failed database queries
   - Exponential backoff
   - Circuit breaker pattern

4. **Performance Monitoring**
   - Track slow queries
   - Alert on excessive query counts
   - Optimize automatically

5. **Better Conflict Resolution**
   - Show diff of changes
   - Allow merging conflicting edits
   - Suggest which change to keep

---

## Summary

The system now includes:

✅ **Optimistic Locking** - Prevents concurrent edit conflicts
✅ **Database Error Handling** - Graceful handling of connection issues
✅ **User-Friendly Error Pages** - Clear, actionable error messages
✅ **Comprehensive Tests** - 15+ test cases covering critical scenarios
✅ **Error Logging** - All errors logged for debugging
✅ **Version Control** - Track changes and detect conflicts
✅ **Middleware Protection** - Catches errors before reaching users

**Result**: Users never see technical error messages. They always know:
- What went wrong (in simple terms)
- Why it matters (impact)
- What to do about it (actions)
- Who to contact (support)

---

**Need Help?**
- Check test output: `./venv/Scripts/python manage.py test -v 2`
- Review error logs: `logs/errors.log`
- Contact IT Support with error code from error page

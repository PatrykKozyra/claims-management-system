## 📡 REST API Endpoints

### Authentication

The API supports multiple authentication methods:

#### 1. Session Authentication (Browser-based)
```bash
# Login first through /login/
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Cookie: sessionid=your_session_cookie"
```

#### 2. Token Authentication
```bash
# Get token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token
curl -X GET http://localhost:8000/api/v1/voyages/ \
  -H "Authorization: Token your_token_here"
```

#### 3. JWT Authentication (Recommended for mobile/SPA)
```bash
# Get JWT token pair
curl -X POST http://localhost:8000/api/v1/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Response: {"access": "...", "refresh": "..."}

# Use access token
curl -X GET http://localhost:8000/api/v1/voyages/ \
  -H "Authorization: Bearer your_access_token"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/jwt/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

---

### Base URL

```
http://localhost:8000/api/v1/
```

---

## Endpoints

### Users

#### List Users
```http
GET /api/v1/users/
```

**Query Parameters:**
- `role` - Filter by role (READ, WRITE, TEAM_LEAD, ADMIN)
- `is_active` - Filter by active status
- `department` - Filter by department
- `search` - Search by username, name, or email
- `ordering` - Order by field (username, date_joined, last_login)

#### Get Current User
```http
GET /api/v1/users/me/
```

#### Get Analysts
```http
GET /api/v1/users/analysts/
```

Returns users who can be assigned voyages/claims (WRITE, TEAM_LEAD, ADMIN roles).

---

### Ship Owners

#### List Ship Owners
```http
GET /api/v1/ship-owners/
```

**Query Parameters:**
- `is_active` - Filter by active status
- `search` - Search by name, code, or email
- `ordering` - Order by field (name, code, created_at)

#### Get Ship Owner Voyages
```http
GET /api/v1/ship-owners/{id}/voyages/
```

#### Get Ship Owner Claims
```http
GET /api/v1/ship-owners/{id}/claims/
```

---

### Voyages

#### List Voyages
```http
GET /api/v1/voyages/
```

**Query Parameters:**
- `assignment_status` - UNASSIGNED, ASSIGNED, COMPLETED
- `charter_type` - SPOT, TRADED
- `ship_owner` - Filter by ship owner ID
- `assigned_analyst` - Filter by analyst ID
- `search` - Search by voyage number, vessel name, IMO, CP
- `ordering` - Order by field (created_at, laycan_start, voyage_number)

#### Get Voyage Detail
```http
GET /api/v1/voyages/{id}/
```

#### Assign Voyage
```http
POST /api/v1/voyages/{id}/assign/
Content-Type: application/json

{
  "analyst_id": 5
}
```

#### Get Unassigned Voyages
```http
GET /api/v1/voyages/unassigned/
```

#### Get My Assigned Voyages
```http
GET /api/v1/voyages/my_assignments/
```

---

### Claims

#### List Claims
```http
GET /api/v1/claims/
```

**Query Parameters:**
- `status` - DRAFT, UNDER_REVIEW, SUBMITTED, SETTLED, REJECTED
- `payment_status` - NOT_SENT, SENT, PARTIALLY_PAID, PAID, TIMEBAR, DISPUTED
- `claim_type` - DEMURRAGE, POST_DEAL, DESPATCH, DEAD_FREIGHT, OTHER
- `voyage` - Filter by voyage ID
- `ship_owner` - Filter by ship owner ID
- `assigned_to` - Filter by assigned user ID
- `is_time_barred` - Filter by time-bar status
- `search` - Search by claim number, RADAR ID, description
- `ordering` - Order by field (created_at, claim_amount, claim_deadline)

#### Create Claim
```http
POST /api/v1/claims/
Content-Type: application/json

{
  "voyage": 1,
  "ship_owner": 2,
  "claim_type": "DEMURRAGE",
  "claim_amount": "50000.00",
  "laytime_used": "72.50",
  "description": "Demurrage claim for excess laytime"
}
```

#### Submit Claim
```http
POST /api/v1/claims/{id}/submit/
```

Changes claim status from DRAFT to SUBMITTED.

#### Add Payment to Claim
```http
POST /api/v1/claims/{id}/add_payment/
Content-Type: application/json

{
  "amount": "25000.00"
}
```

#### Get Time-Barred Claims
```http
GET /api/v1/claims/timebarred/
```

#### Get My Claims
```http
GET /api/v1/claims/my_claims/
```

#### Get Claims Analytics
```http
GET /api/v1/claims/analytics/
```

Returns aggregated statistics about claims.

**Response:**
```json
{
  "total_claims": 150,
  "total_amount": "5250000.00",
  "paid_amount": "3100000.00",
  "outstanding_amount": "2150000.00",
  "by_status": {
    "DRAFT": 20,
    "SUBMITTED": 80,
    "SETTLED": 50
  },
  "by_payment_status": {
    "PAID": 50,
    "PARTIALLY_PAID": 30,
    "NOT_SENT": 70
  },
  "timebarred_claims": 5
}
```

---

### Comments

#### List Comments
```http
GET /api/v1/comments/
```

**Query Parameters:**
- `claim` - Filter by claim ID
- `user` - Filter by user ID

#### Create Comment
```http
POST /api/v1/comments/
Content-Type: application/json

{
  "claim": 1,
  "content": "This claim needs additional documentation."
}
```

---

### Documents

#### List Documents
```http
GET /api/v1/documents/
```

**Query Parameters:**
- `claim` - Filter by claim ID
- `document_type` - CHARTER_PARTY, SOF, LAYTIME_CALC, etc.
- `uploaded_by` - Filter by uploader ID

#### Upload Document
```http
POST /api/v1/documents/
Content-Type: multipart/form-data

claim: 1
title: "Statement of Facts"
document_type: "SOF"
file: <file data>
description: "Final SOF agreed with charterers"
```

---

### Ships

#### List Ships
```http
GET /api/v1/ships/
```

**Query Parameters:**
- `is_time_charter` - Filter by TC status
- `ship_type` - Filter by ship type
- `flag` - Filter by flag
- `search` - Search by IMO, vessel name, owner
- `ordering` - Order by field (vessel_name, built_year, dwt)

#### Get Active Time Charters
```http
GET /api/v1/ships/active_charters/
```

---

### Port Activities

#### List Port Activities
```http
GET /api/v1/port-activities/
```

**Query Parameters:**
- `ship` - Filter by ship ID
- `voyage` - Filter by voyage ID
- `activity_type` - Filter by activity type ID
- `start_date_status` - ESTIMATED, ACTUAL
- `end_date_status` - ESTIMATED, ACTUAL

#### Get Ship Timeline
```http
GET /api/v1/port-activities/ship_timeline/?ship_id=1
```

Returns chronological timeline of activities for a specific ship.

---

### Activity Types

#### List Activity Types
```http
GET /api/v1/activity-types/
```

**Query Parameters:**
- `category` - Filter by category (CARGO_OPS, BALLASTING, etc.)
- `is_active` - Filter by active status
- `search` - Search by code, name, description

---

### Activity Logs (Read-Only)

#### List Activity Logs
```http
GET /api/v1/activity-logs/
```

**Query Parameters:**
- `claim` - Filter by claim ID
- `user` - Filter by user ID
- `action` - Filter by action type

---

## Response Format

### Success Response
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2"
}
```

### List Response
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/voyages/?page=2",
  "previous": null,
  "results": [
    {"id": 1, "...": "..."},
    {"id": 2, "...": "..."}
  ]
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

---

## Pagination

All list endpoints support pagination:

```http
GET /api/v1/voyages/?page=2
GET /api/v1/voyages/?page_size=50
```

---

## Filtering & Searching

### Filter by Field
```http
GET /api/v1/claims/?status=SUBMITTED
GET /api/v1/claims/?payment_status=PAID
```

### Multiple Filters
```http
GET /api/v1/claims/?status=SUBMITTED&payment_status=SENT&assigned_to=5
```

### Search
```http
GET /api/v1/voyages/?search=MV%20Atlantic
```

### Ordering
```http
GET /api/v1/claims/?ordering=-created_at
GET /api/v1/claims/?ordering=claim_amount,-created_at
```

---

## Rate Limiting

API endpoints are rate-limited:
- **Authentication**: 5 attempts per 5 minutes
- **Exports**: 10 per hour
- **General**: 1000 requests per hour per user

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1641234567
```

---

## API Versioning

Current API version: **v1**

The API uses URL path versioning:
```
/api/v1/
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests (Rate Limited) |
| 500 | Internal Server Error |

---

## Examples

### Create a Complete Claim

```bash
# 1. Create claim
curl -X POST http://localhost:8000/api/v1/claims/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voyage": 1,
    "ship_owner": 2,
    "claim_type": "DEMURRAGE",
    "claim_amount": "75000.00",
    "laytime_used": "96.5",
    "description": "Demurrage claim for delays at discharge port",
    "claim_deadline": "2026-06-30"
  }'

# 2. Add comment
curl -X POST http://localhost:8000/api/v1/comments/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": 1,
    "content": "Awaiting charterer response on time calculation"
  }'

# 3. Submit claim
curl -X POST http://localhost:8000/api/v1/claims/1/submit/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Record payment
curl -X POST http://localhost:8000/api/v1/claims/1/add_payment/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "37500.00"
  }'
```

### Get Dashboard Data

```bash
# Get my assignments
curl -X GET "http://localhost:8000/api/v1/voyages/my_assignments/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get my claims
curl -X GET "http://localhost:8000/api/v1/claims/my_claims/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get analytics
curl -X GET "http://localhost:8000/api/v1/claims/analytics/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Testing the API

### Using cURL
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.token')

# Use token
curl -X GET http://localhost:8000/api/v1/voyages/ \
  -H "Authorization: Token $TOKEN"
```

### Using Python
```python
import requests

# Get token
response = requests.post(
    'http://localhost:8000/api/v1/auth/token/',
    json={'username': 'admin', 'password': 'password'}
)
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Token {token}'}
voyages = requests.get(
    'http://localhost:8000/api/v1/voyages/',
    headers=headers
).json()
```

### Using JavaScript (Fetch API)
```javascript
// Get token
const response = await fetch('http://localhost:8000/api/v1/auth/jwt/create/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: 'password'})
});
const {access} = await response.json();

// Make authenticated request
const voyages = await fetch('http://localhost:8000/api/v1/voyages/', {
  headers: {'Authorization': `Bearer ${access}`}
}).then(r => r.json());
```

---

## Interactive API Documentation

Once the server is running, visit:

- **Browsable API**: http://localhost:8000/api/v1/
- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/

---

*Last Updated: January 3, 2026*
# REST API - Ready to Use!

**Status**: ✅ ALL SYSTEMS GO!

The REST API has been successfully configured and is now ready to use.

---

## Quick Access Links

Your server is running on **http://localhost:8005/**

| Feature | URL | Status |
|---------|-----|--------|
| **Main Application** | http://localhost:8005/ | ✅ Running |
| **REST API Root** | http://localhost:8005/api/v1/ | ✅ Ready |
| **Swagger UI** | http://localhost:8005/api/schema/swagger-ui/ | ✅ Ready |
| **ReDoc** | http://localhost:8005/api/schema/redoc/ | ✅ Ready |
| **Admin Panel** | http://localhost:8005/admin/ | ✅ Ready |

---

## What Was Just Fixed

### 1. Added Swagger/ReDoc URLs ✅
```python
# Added to claims_system/urls.py
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # ... existing URLs ...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### 2. Added Django REST Framework to INSTALLED_APPS ✅
```python
INSTALLED_APPS = [
    # ... Django apps ...
    # REST Framework
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_spectacular',
    # Celery
    'django_celery_beat',
    'django_celery_results',
    # Project apps
    'claims',
    'ships',
    'port_activities',
]
```

### 3. Added REST Framework Configuration ✅
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

### 4. Applied Database Migrations ✅
Successfully applied 39 migrations for:
- `authtoken` - Token authentication tables
- `django_celery_beat` - Periodic task scheduler tables
- `django_celery_results` - Task result storage tables

### 5. Server Auto-Reloaded ✅
The Django development server detected the changes and automatically reloaded.

---

## How to Test the API

### Method 1: Use Your Web Browser (Easiest!)

1. **Open** http://localhost:8005/api/v1/ in your browser
2. **Log in** when prompted with: `admin` / `admin123`
3. **Browse** the API endpoints interactively!

You'll see a beautiful browsable API interface where you can:
- Click on endpoints to view them
- Make POST/PUT/DELETE requests via forms
- See formatted JSON responses
- Filter and search data

### Method 2: Get a JWT Token (For API Clients)

**Step 1: Get a token**
```bash
curl -X POST http://localhost:8005/api/v1/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Step 2: Use the token**
```bash
curl http://localhost:8005/api/v1/voyages/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Method 3: Interactive API Documentation

**Swagger UI**: http://localhost:8005/api/schema/swagger-ui/
- Click "Authorize" button
- Enter: `Bearer YOUR_JWT_TOKEN`
- Click any endpoint → "Try it out" → "Execute"

**ReDoc**: http://localhost:8005/api/schema/redoc/
- Clean, searchable documentation
- Shows all request/response schemas
- Perfect for developers

---

## Available API Endpoints

### Authentication
- `POST /api/v1/auth/jwt/create/` - Get JWT token
- `POST /api/v1/auth/jwt/refresh/` - Refresh JWT token
- `POST /api/v1/auth/jwt/verify/` - Verify JWT token
- `POST /api/v1/auth/token/` - Get auth token

### Users
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/me/` - Current user info
- `GET /api/v1/users/analysts/` - Get analysts for assignment

### Voyages
- `GET /api/v1/voyages/` - List voyages (with filtering)
- `GET /api/v1/voyages/{id}/` - Voyage details
- `POST /api/v1/voyages/{id}/assign/` - Assign to analyst
- `GET /api/v1/voyages/unassigned/` - Unassigned voyages
- `GET /api/v1/voyages/my_assignments/` - My assigned voyages

### Claims
- `GET /api/v1/claims/` - List claims (with filtering)
- `POST /api/v1/claims/` - Create claim
- `GET /api/v1/claims/{id}/` - Claim details
- `PUT /api/v1/claims/{id}/` - Update claim
- `PATCH /api/v1/claims/{id}/` - Partial update
- `DELETE /api/v1/claims/{id}/` - Delete claim
- `POST /api/v1/claims/{id}/submit/` - Submit claim
- `POST /api/v1/claims/{id}/add_payment/` - Add payment
- `GET /api/v1/claims/timebarred/` - Time-barred claims
- `GET /api/v1/claims/my_claims/` - My claims
- `GET /api/v1/claims/analytics/` - Claims analytics

### Ship Owners
- `GET /api/v1/ship-owners/` - List ship owners
- `GET /api/v1/ship-owners/{id}/` - Ship owner details
- `GET /api/v1/ship-owners/{id}/voyages/` - Owner's voyages
- `GET /api/v1/ship-owners/{id}/claims/` - Owner's claims

### Ships & Port Activities
- `GET /api/v1/ships/` - List ships
- `GET /api/v1/ships/active_charters/` - Active time charters
- `GET /api/v1/port-activities/` - List port activities
- `GET /api/v1/port-activities/ship_timeline/?ship_id=1` - Ship timeline

### Comments & Documents
- `GET /api/v1/comments/` - List comments
- `POST /api/v1/comments/` - Add comment
- `GET /api/v1/documents/` - List documents
- `POST /api/v1/documents/` - Upload document

### Activity Logs
- `GET /api/v1/activity-logs/` - List activity logs (read-only)

---

## Python Usage Example

```python
import requests

# 1. Get JWT token
response = requests.post(
    'http://localhost:8005/api/v1/auth/jwt/create/',
    json={'username': 'admin', 'password': 'admin123'}
)
token = response.json()['access']

# 2. Set up headers
headers = {'Authorization': f'Bearer {token}'}

# 3. Get all claims
claims = requests.get(
    'http://localhost:8005/api/v1/claims/',
    headers=headers
).json()

print(f"Total claims: {claims['count']}")
for claim in claims['results']:
    print(f"  - {claim['claim_number']}: ${claim['claim_amount']}")

# 4. Create a new claim
new_claim = requests.post(
    'http://localhost:8005/api/v1/claims/',
    headers=headers,
    json={
        'voyage': 1,
        'ship_owner': 2,
        'claim_type': 'DEMURRAGE',
        'claim_amount': '50000.00',
        'description': 'Test claim via API'
    }
).json()

print(f"Created claim: {new_claim['claim_number']}")

# 5. Filter claims by status
submitted_claims = requests.get(
    'http://localhost:8005/api/v1/claims/?status=SUBMITTED',
    headers=headers
).json()

print(f"Submitted claims: {submitted_claims['count']}")
```

---

## JavaScript/Fetch Example

```javascript
// 1. Get JWT token
const response = await fetch('http://localhost:8005/api/v1/auth/jwt/create/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: 'admin123'})
});
const {access} = await response.json();

// 2. Fetch claims
const claimsResponse = await fetch('http://localhost:8005/api/v1/claims/', {
  headers: {'Authorization': `Bearer ${access}`}
});
const claims = await claimsResponse.json();

console.log(`Total claims: ${claims.count}`);
claims.results.forEach(claim => {
  console.log(`${claim.claim_number}: $${claim.claim_amount}`);
});
```

---

## Filtering & Searching

The API supports powerful filtering and searching:

### Filter Examples
```bash
# Filter by status
GET /api/v1/claims/?status=SUBMITTED

# Filter by payment status
GET /api/v1/claims/?payment_status=PAID

# Filter by assigned analyst
GET /api/v1/claims/?assigned_to=5

# Multiple filters
GET /api/v1/claims/?status=SUBMITTED&payment_status=SENT

# Order results
GET /api/v1/claims/?ordering=-created_at

# Search by vessel name
GET /api/v1/claims/?search=Atlantic

# Pagination
GET /api/v1/claims/?page=2
```

---

## What's Working Now

✅ **REST API** - All endpoints configured and working
✅ **JWT Authentication** - Token-based auth ready
✅ **Session Authentication** - Browser login works
✅ **Token Authentication** - API token auth available
✅ **Browsable API** - Beautiful web interface
✅ **Swagger UI** - Interactive documentation
✅ **ReDoc** - Clean API docs
✅ **Filtering** - django-filter integration
✅ **Pagination** - 25 items per page
✅ **Permissions** - Role-based access control
✅ **Database** - All migrations applied
✅ **Server** - Running on port 8005

---

## Optional: Celery Setup

If you want background tasks (RADAR sync, scheduled time-bar checks, etc.):

### Requirements
- Redis server must be installed and running

### Setup Steps

**1. Install Redis** (if not already installed)
- Windows: Download from https://github.com/microsoftarchive/redis/releases
- Or use WSL: `wsl sudo apt-get install redis-server`

**2. Start Redis** (in a new terminal)
```bash
wsl redis-server
# Or on Linux/Mac:
redis-server
```

**3. Start Celery Worker** (in a new terminal)
```bash
celery -A claims_system worker -l info
```

**4. Start Celery Beat Scheduler** (in a new terminal)
```bash
celery -A claims_system beat -l info
```

**Note**: Celery is **optional**. The app works perfectly without it - tasks just run synchronously instead of in the background.

---

## Testing Checklist

- [ ] Open http://localhost:8005/api/v1/ in browser
- [ ] Log in with admin/admin123
- [ ] Browse the API endpoints
- [ ] Click on "claims" endpoint
- [ ] See the list of claims in JSON format
- [ ] Try the filter button to filter claims
- [ ] Open http://localhost:8005/api/schema/swagger-ui/
- [ ] Test JWT authentication with curl/Postman
- [ ] Try creating a claim via API

---

## Next Steps

1. **Test the API** in your browser at http://localhost:8005/api/v1/
2. **Explore Swagger UI** at http://localhost:8005/api/schema/swagger-ui/
3. **Try the Python example** above
4. **Build integrations** - The API is ready for mobile apps, external systems, etc.
5. **(Optional)** Set up Celery if you need background tasks

---

## Troubleshooting

### If you see "404 Not Found"
- Make sure the server is running on port 8005
- Check that you're using the correct URL: http://localhost:8005/api/v1/

### If you see "401 Unauthorized"
- You need to log in first (browser) or provide a valid JWT token
- Use the browsable API in your browser for easier testing

### If you see "Template Not Found"
- This has been fixed! Restart your browser and clear cache.

---

**🎉 Your REST API is fully operational!**

For detailed API documentation, see [NEW_FEATURES_GUIDE.md](NEW_FEATURES_GUIDE.md)

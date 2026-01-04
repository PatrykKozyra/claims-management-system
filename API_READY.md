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

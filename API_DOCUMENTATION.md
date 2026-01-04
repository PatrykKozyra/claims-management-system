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

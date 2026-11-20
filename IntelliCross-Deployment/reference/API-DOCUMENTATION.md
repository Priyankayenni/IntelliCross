# 📖 API DOCUMENTATION

**Complete API Reference for IntelliCross Backend**

---

## 🔌 Base URL

```
https://your-backend.onrender.com
```

All API requests must include:
- `Content-Type: application/json`
- `Authorization: Bearer {JWT_TOKEN}` (except for public endpoints)

---

## 🔐 Authentication Endpoints

### POST /api/auth/signup
Create a new user account

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Error (400):**
```json
{
  "error": "Email already exists",
  "code": "DUPLICATE_EMAIL"
}
```

---

### POST /api/auth/login
Authenticate and get JWT token

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "expires_in": 86400
}
```

**Error (401):**
```json
{
  "error": "Invalid credentials",
  "code": "INVALID_CREDENTIALS"
}
```

---

### POST /api/auth/logout
Logout and invalidate token

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

### POST /api/auth/refresh
Refresh JWT token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

---

## 📊 Detection Endpoints

### GET /api/detections
List all detections with pagination

**Query Parameters:**
- `limit` (default: 50, max: 100)
- `offset` (default: 0)
- `type` (filter by detection type)
- `since` (ISO timestamp)

**Request:**
```bash
curl "https://your-backend.onrender.com/api/detections?limit=10&offset=0" \
  -H "Authorization: Bearer {TOKEN}"
```

**Response (200 OK):**
```json
{
  "detections": [
    {
      "id": "det-123",
      "type": "vehicle",
      "confidence": 0.95,
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "image_url": "https://...",
      "created_at": "2024-01-01T12:00:00Z",
      "created_by": "user-123"
    }
  ],
  "total": 1500,
  "limit": 10,
  "offset": 0
}
```

---

### POST /api/detections
Create a new detection record

**Request:**
```json
{
  "type": "vehicle",
  "confidence": 0.95,
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "image_url": "https://...",
  "metadata": {
    "camera_id": "cam-1",
    "vehicle_color": "red"
  }
}
```

**Response (201 Created):**
```json
{
  "id": "det-123",
  "type": "vehicle",
  "confidence": 0.95,
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### GET /api/detections/{id}
Get specific detection details

**Request:**
```bash
curl "https://your-backend.onrender.com/api/detections/det-123" \
  -H "Authorization: Bearer {TOKEN}"
```

**Response (200 OK):**
```json
{
  "id": "det-123",
  "type": "vehicle",
  "confidence": 0.95,
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "image_url": "https://...",
  "metadata": {
    "camera_id": "cam-1"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "created_by": "user-123"
}
```

---

## 🚨 Alert Endpoints

### GET /api/alerts
List user's alerts

**Query Parameters:**
- `status` (pending, acknowledged, resolved)
- `severity` (low, medium, high, critical)
- `limit` (default: 50)

**Request:**
```bash
curl "https://your-backend.onrender.com/api/alerts?status=pending" \
  -H "Authorization: Bearer {TOKEN}"
```

**Response (200 OK):**
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "type": "accident",
      "severity": "high",
      "status": "pending",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "hospital_id": "hosp-123",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:05:00Z"
    }
  ],
  "total": 5
}
```

---

### POST /api/alerts
Create a new alert

**Request:**
```json
{
  "type": "accident",
  "severity": "high",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "detection_id": "det-123",
  "hospital_id": "hosp-123"
}
```

**Response (201 Created):**
```json
{
  "id": "alert-123",
  "type": "accident",
  "severity": "high",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### PUT /api/alerts/{id}
Update alert status

**Request:**
```json
{
  "status": "acknowledged",
  "notes": "Emergency team notified"
}
```

**Response (200 OK):**
```json
{
  "id": "alert-123",
  "status": "acknowledged",
  "updated_at": "2024-01-01T12:05:00Z"
}
```

---

## 🏥 Hospital Endpoints

### GET /api/hospitals
List nearby hospitals

**Query Parameters:**
- `latitude` (required)
- `longitude` (required)
- `radius_km` (default: 10)

**Request:**
```bash
curl "https://your-backend.onrender.com/api/hospitals?latitude=40.7128&longitude=-74.0060&radius_km=5"
```

**Response (200 OK):**
```json
{
  "hospitals": [
    {
      "id": "hosp-123",
      "name": "City Medical Center",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.0060
      },
      "phone": "+1-555-0100",
      "bed_capacity": 500,
      "available_beds": 45,
      "distance_km": 2.3,
      "est_time_minutes": 8
    }
  ]
}
```

---

### GET /api/hospitals/{id}
Get hospital details

**Response (200 OK):**
```json
{
  "id": "hosp-123",
  "name": "City Medical Center",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "phone": "+1-555-0100",
  "departments": ["Emergency", "Surgery", "ICU"],
  "bed_capacity": 500,
  "available_beds": 45,
  "specialties": ["Trauma", "Cardiology"]
}
```

---

## 📊 Analytics Endpoints

### GET /api/analytics/summary
Get statistics summary

**Query Parameters:**
- `time_range` (today, week, month)

**Request:**
```bash
curl "https://your-backend.onrender.com/api/analytics/summary?time_range=week" \
  -H "Authorization: Bearer {TOKEN}"
```

**Response (200 OK):**
```json
{
  "total_detections": 1250,
  "total_alerts": 45,
  "critical_alerts": 3,
  "average_response_time_minutes": 8.5,
  "hospitals_involved": 12,
  "detections_by_type": {
    "vehicle": 750,
    "pedestrian": 300,
    "obstacle": 200
  }
}
```

---

### GET /api/analytics/timeline
Get time-series data

**Query Parameters:**
- `start_date` (ISO date)
- `end_date` (ISO date)
- `interval` (hourly, daily, weekly)

**Response (200 OK):**
```json
{
  "timeline": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "detections": 125,
      "alerts": 5,
      "critical_alerts": 1
    }
  ]
}
```

---

## 🔍 Health Endpoints

### GET /health
System health check (no auth required)

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime_seconds": 3600
}
```

---

### GET /api/health
Detailed health check

**Response (200 OK):**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "database": "connected",
  "cache": "connected",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## ❌ Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## 🔄 Rate Limiting

- **Requests per minute:** 60
- **Requests per hour:** 3600
- **Burst limit:** 10 requests per second

Response headers include:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Reset timestamp

---

## 🧪 Example Usage (JavaScript/Fetch)

```javascript
// Login
const loginResponse = await fetch('https://your-backend.onrender.com/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
})
const { token } = await loginResponse.json()

// Get detections
const detectionsResponse = await fetch('https://your-backend.onrender.com/api/detections', {
  headers: { 'Authorization': `Bearer ${token}` }
})
const { detections } = await detectionsResponse.json()

// Create alert
const alertResponse = await fetch('https://your-backend.onrender.com/api/alerts', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    type: 'accident',
    severity: 'high',
    location: { latitude: 40.7128, longitude: -74.0060 }
  })
})
const newAlert = await alertResponse.json()
```

---

## 📚 Additional Resources

- [OpenAPI Spec](./openapi.yaml)
- [Postman Collection](./IntelliCross.postman_collection.json)
- [API Webhooks](./webhooks.md)
- [WebSocket Events](./websocket.md)

---

**Next:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common API issues

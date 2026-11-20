# 🏛️ SYSTEM ARCHITECTURE

**Complete System Architecture & Data Flow**

---

## 📐 Overall Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                    (React Frontend - Vercel)                      │
│                                                                   │
│  ┌─────────────┬──────────────┬──────────────┬─────────────────┐ │
│  │   Dashboard │  Video Feed  │  Alerts Panel│  Map Integration│ │
│  │  - Stats    │  - Live Feed │  - Incidents │  - Hospital     │ │
│  │  - History  │  - Detection │  - Responses │    Location     │ │
│  │  - Reports  │  - Analysis  │  - History   │  - Routes       │ │
│  └─────────────┴──────────────┴──────────────┴─────────────────┘ │
│                                                                   │
│  Real-time Updates via WebSocket & REST API Calls               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                        🔗 API Layer 🔗
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    API SERVER (FastAPI - Render)                 │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  API Endpoints                           │   │
│  │  - /api/health         - System health check             │   │
│  │  - /api/detect         - Submit detection data           │   │
│  │  - /api/detections     - Query detections                │   │
│  │  - /api/alerts         - Alert management                │   │
│  │  - /api/hospitals      - Hospital locations              │   │
│  │  - /api/auth/*         - Authentication                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Business Logic & Processing                   │   │
│  │  - Detection Algorithm (YOLOv8)                          │   │
│  │  - Alert Generation & Routing                            │   │
│  │  - User Authentication & Authorization                   │   │
│  │  - Data Validation & Transformation                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Background Jobs & Workers                     │   │
│  │  - Detection Processing Queue                            │   │
│  │  - Alert Notifications                                   │   │
│  │  - Data Aggregation & Analytics                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  SQL Queries & Transactions                                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                   🗄️ Database Layer 🗄️
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL - Supabase)                    │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │    Users     │  │  Detections  │  │    Alerts    │           │
│  │              │  │              │  │              │           │
│  │ - user_id    │  │ - detect_id  │  │ - alert_id   │           │
│  │ - email      │  │ - timestamp  │  │ - user_id    │           │
│  │ - password   │  │ - type       │  │ - type       │           │
│  │ - role       │  │ - location   │  │ - status     │           │
│  │ - hospitals  │  │ - confidence │  │ - created_at │           │
│  │ - created_at │  │ - image_url  │  │ - updated_at │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Hospitals   │  │    Routes    │  │  Analytics   │           │
│  │              │  │              │  │              │           │
│  │ - hospital_id│  │ - route_id   │  │ - metric_id  │           │
│  │ - name       │  │ - from_loc   │  │ - metric_name│           │
│  │ - location   │  │ - to_loc     │  │ - value      │           │
│  │ - phone      │  │ - distance   │  │ - timestamp  │           │
│  │ - capacity   │  │ - est_time   │  │ - dimension  │           │
│  │ - available  │  │ - status     │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                   │
│  Backups, Replication, Security Policies                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagrams

### Detection Processing Flow

```
Video Input
    │
    ▼
┌──────────────────────────┐
│  Frontend Video Player   │
│  - Capture frames        │
│  - Send to backend       │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Backend Detection API   │
│  - /api/detect endpoint  │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  YOLOv8 Model            │
│  - Process image         │
│  - Detect objects        │
│  - Generate predictions  │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Validation & Filtering  │
│  - Confidence threshold  │
│  - Classify type         │
│  - Location mapping      │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Save to Database        │
│  - detections table      │
│  - store metadata        │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Generate Alert (if needed)
│  - Check rules           │
│  - Create alert record   │
│  - Notify recipients     │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│  Push to Frontend        │
│  - Real-time update      │
│  - WebSocket broadcast   │
│  - Refresh dashboard     │
└──────────────────────────┘
```

### Alert Generation & Notification Flow

```
Detection Created
    │
    ▼
┌─────────────────────────────────┐
│  Alert Rules Engine             │
│  - Evaluate rules               │
│  - Check severity               │
│  - Determine recipients         │
└──────────────┬──────────────────┘
               │
               ▼
         Alert Created?
           /        \
         YES        NO
         │          │
         ▼          ▼
    Proceed    End Process
         │
         ▼
┌─────────────────────────────────┐
│  Alert Storage                  │
│  - Save to database             │
│  - Set status = PENDING         │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Notification Queue             │
│  - Add to queue                 │
│  - Set priority                 │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Send Notifications             │
│  - Email                        │
│  - SMS                          │
│  - App notification             │
│  - Dashboard alert              │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Update Frontend                │
│  - Broadcast to all users       │
│  - Show in alerts panel         │
│  - Add to timeline              │
└─────────────────────────────────┘
```

### Authentication Flow

```
User Login Request
    │
    ▼
┌─────────────────────┐
│  Validate Inputs    │
│  - Email format     │
│  - Password present │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Check Database     │
│  - Find user record │
└──────────┬──────────┘
           │
    User Found?
      /    \
     YES   NO
     │      └──▶ Return 401 Error
     │
     ▼
┌─────────────────────┐
│  Verify Password    │
│  - Hash check       │
│  - Compare          │
└──────────┬──────────┘
           │
    Password Correct?
      /         \
     YES        NO
     │           └──▶ Return 401 Error
     │
     ▼
┌─────────────────────┐
│  Generate JWT       │
│  - User claims      │
│  - Expiration       │
│  - Sign token       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Return Token       │
│  - Send to client   │
│  - Store in cookie  │
└──────────┬──────────┘
           │
           ▼
Frontend stores JWT & adds to all API requests
```

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50),  -- admin, operator, viewer
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Detections Table
```sql
CREATE TABLE detections (
    detect_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    detection_type VARCHAR(100),  -- vehicle, pedestrian, obstacle
    confidence FLOAT,
    location POINT,  -- latitude, longitude
    image_url VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP
);
```

### Alerts Table
```sql
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    detect_id UUID REFERENCES detections(detect_id),
    alert_type VARCHAR(100),  -- accident, congestion, hazard
    severity VARCHAR(50),  -- low, medium, high, critical
    status VARCHAR(50),  -- pending, acknowledged, resolved
    hospital_id UUID,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Hospitals Table
```sql
CREATE TABLE hospitals (
    hospital_id UUID PRIMARY KEY,
    name VARCHAR(255),
    location POINT,  -- latitude, longitude
    phone VARCHAR(20),
    bed_capacity INTEGER,
    available_beds INTEGER,
    updated_at TIMESTAMP
);
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────┐
│        SSL/TLS Encryption               │
│  (All data in transit encrypted)        │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Frontend       API Server     Database
(HTTPS)        (HTTPS)     (Encrypted)
    │              │              │
    └──────────────┼──────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Authentication & Authorization    │
│  - JWT tokens                           │
│  - Role-based access control            │
│  - Session management                   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Data Protection                   │
│  - Password hashing (bcrypt)            │
│  - Sensitive field encryption           │
│  - SQL injection prevention             │
│  - CORS policies                        │
└─────────────────────────────────────────┘
```

---

## 🚀 Scaling Architecture

### Horizontal Scaling

```
Load Balancer (Vercel/Render)
        │
    ┌───┼───┐
    │   │   │
    ▼   ▼   ▼
  API1 API2 API3  (Multiple backend instances)
    │   │   │
    └───┼───┘
        │
    Database (Single source of truth)
```

### Caching Strategy

```
Frontend Cache
    │
    ▼
API Cache Layer
    │
    ▼
Database
```

---

## 📊 Performance Considerations

### Frontend Optimization
- Code splitting with Vite
- Image lazy loading
- Minified assets
- CDN distribution (Vercel automatic)

### Backend Optimization
- Database indexing
- Query optimization
- Connection pooling
- Background task processing

### Database Optimization
- Proper indexing
- Query optimization
- Data archival
- Backup strategy

---

## 🔄 Deployment Architecture

```
GitHub Repository
    │
    ├──▶ CI/CD Pipeline (GitHub Actions)
    │        │
    │        ├──▶ Run Tests
    │        ├──▶ Build & Lint
    │        └──▶ Deploy if success
    │              │
    │              ├──▶ Build backend image
    │              │        │
    │              │        ▼
    │              └──▶ Deploy to Render
    │                   (API Server)
    │
    └──▶ Deploy Frontend
             │
             ▼
         Vercel
         (React App)

Both connect to Supabase Database
```

---

## 📚 Technology Justification

| Technology | Why Chosen |
|-----------|-----------|
| React | Fast, component-based, large ecosystem |
| TypeScript | Type safety, better IDE support |
| Vite | Fast build, fast HMR |
| FastAPI | Fast, modern, async support |
| PostgreSQL | Reliable, powerful, free tier available |
| Supabase | PostgreSQL + Auth + Real-time |
| Vercel | Optimal React hosting, auto-scaling |
| Render | Simple backend deployment |
| Docker | Consistency across environments |
| YOLOv8 | State-of-art object detection |

---

## 🎯 Key Metrics

| Metric | Target |
|--------|--------|
| Frontend Load Time | < 3 seconds |
| API Response Time | < 500ms |
| Detection Processing | < 2 seconds |
| Alert Notification | < 1 second |
| Database Query | < 100ms |
| Uptime | 99.9% |

---

## 📖 Next Steps

1. Review [SYSTEM-ARCHITECTURE.md](SYSTEM-ARCHITECTURE.md) (this file)
2. Study [IntelliCross-Deployment-Guide.md](IntelliCross-Deployment-Guide.md)
3. Follow [../DEPLOYMENT-ACTION-PLAN.md](../DEPLOYMENT-ACTION-PLAN.md)

---

*IntelliCross System Architecture v1.0*

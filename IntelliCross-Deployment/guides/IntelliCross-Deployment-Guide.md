# 📘 IntelliCross Deployment Guide

**Complete Technical Deployment Guide**

---

## 🎯 Overview

IntelliCross is a modern full-stack application designed for intelligent traffic and incident detection with real-time emergency coordination. This guide covers the complete technical deployment process.

---

## 🏗️ Technology Stack

### Frontend
- **Framework:** React 18+ with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State Management:** React Context + Hooks
- **Real-time:** WebSocket support
- **Database Client:** Supabase JS SDK

### Backend
- **Framework:** FastAPI (Python 3.9+)
- **Server:** Uvicorn
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Authentication:** JWT tokens
- **ML Model:** YOLOv8 (Object Detection)

### Infrastructure
- **Frontend Hosting:** Vercel
- **Backend Hosting:** Render
- **Database:** Supabase (PostgreSQL)
- **Container:** Docker
- **CI/CD:** GitHub Actions

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────┐
│         Frontend (React)                 │
│  - Dashboard                             │
│  - Video Feed                            │
│  - Alerts Panel                          │
│  - Map Integration                       │
│  (Deployed on Vercel)                   │
└────────────────┬────────────────────────┘
                 │ API Calls (REST)
                 │
┌────────────────▼────────────────────────┐
│    Backend (FastAPI)                    │
│  - API Endpoints                        │
│  - Authentication                       │
│  - Detection Processing                 │
│  - Alert Management                     │
│  (Deployed on Render)                   │
└────────────────┬────────────────────────┘
                 │ SQL Queries
                 │
┌────────────────▼────────────────────────┐
│  Database (PostgreSQL)                  │
│  - Users                                │
│  - Detection Records                    │
│  - Alerts                               │
│  - Hospital Data                        │
│  (Hosted on Supabase)                   │
└─────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Deployment

### Step 1: Prerequisites

Ensure you have:
- Node.js 16+ installed locally
- Python 3.9+ installed locally
- Git configured
- GitHub account
- Vercel account
- Render account
- Supabase account

### Step 2: Clone Repository

```bash
git clone https://github.com/your-username/IntelliCross.git
cd IntelliCross
```

### Step 3: Install Dependencies

**Frontend:**
```bash
npm install
npm run build
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Environment Setup

**Frontend (.env):**
```env
VITE_API_URL=https://backend-url.onrender.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-anon-public-key
VITE_ENVIRONMENT=production
```

**Backend (.env):**
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
ENVIRONMENT=production
DEBUG=false
```

### Step 5: Database Setup

1. **Create Supabase project**
   - Go to https://supabase.com
   - Create new project
   - Wait for initialization

2. **Get connection details**
   - In Supabase: Settings > Database > Connection string
   - Add to `backend/.env` as `DATABASE_URL`

3. **Run migrations**
   ```bash
   cd backend
   python -m alembic upgrade head
   ```

### Step 6: Deploy Backend

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy configuration"
   git push origin main
   ```

2. **Create Render Service**
   - Go to https://render.com
   - Create new Web Service
   - Connect your GitHub repo
   - Select `backend` directory
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`

3. **Set Environment Variables**
   - Add all variables from `backend/.env`
   - Deploy

4. **Note Backend URL**
   - Format: `https://your-service.onrender.com`

### Step 7: Deploy Frontend

1. **Update Environment Variables**
   ```bash
   # Update .env with your Render backend URL
   VITE_API_URL=https://your-service.onrender.com
   ```

2. **Create Vercel Deployment**
   - Go to https://vercel.com
   - Import from GitHub
   - Select your repository
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Set Environment Variables**
   - Add all variables from `.env`
   - Deploy

4. **Note Frontend URL**
   - Format: `https://your-project.vercel.app`

### Step 8: Configure CORS

Update `backend/main.py` CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-project.vercel.app",
        "http://localhost:5173"  # for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 9: Test Deployment

```bash
# Test backend health
curl https://your-service.onrender.com/health

# Test API endpoints
curl https://your-service.onrender.com/api/status

# Open frontend in browser
https://your-project.vercel.app
```

---

## 📦 Docker Deployment (Alternative)

### Build Docker Images

```bash
# Backend
docker build -f docker/Dockerfile -t intellicross-backend .

# Frontend
docker build -f docker/Dockerfile.frontend -t intellicross-frontend .
```

### Run Locally

```bash
docker-compose -f docker/docker-compose.yml up
```

### Deploy to Container Registry

```bash
# Push to Docker Hub
docker push your-username/intellicross-backend
docker push your-username/intellicross-frontend

# Or use: Render, Heroku, AWS ECR, etc.
```

---

## 🔄 CI/CD Pipeline

GitHub Actions automatically:
1. Runs tests on push
2. Builds Docker images
3. Deploys to Render (backend)
4. Deploys to Vercel (frontend)
5. Runs security checks

See: `cicd/github-actions-deploy.yml`

---

## 📡 API Endpoints

### Health & Status
```
GET /health → {status: "healthy"}
GET /api/status → {status: "operational", version: "1.0.0"}
```

### Detection
```
POST /api/detect → Submit detection data
GET /api/detections → Get all detections
GET /api/detections/{id} → Get specific detection
```

### Alerts
```
GET /api/alerts → List all alerts
POST /api/alerts → Create alert
PUT /api/alerts/{id} → Update alert
```

### Authentication
```
POST /api/auth/login → User login
POST /api/auth/signup → User registration
POST /api/auth/logout → User logout
```

See: [API-DOCUMENTATION.md](../reference/API-DOCUMENTATION.md) for complete documentation

---

## 🔐 Security Checklist

- [ ] SSL/HTTPS enabled (automatic on both platforms)
- [ ] Environment variables properly configured
- [ ] No hardcoded secrets in code
- [ ] Database backups enabled
- [ ] Supabase RLS policies configured
- [ ] CORS properly restricted
- [ ] API keys rotated periodically
- [ ] Monitoring and alerting set up

---

## 📊 Monitoring

### Vercel
- Real-time analytics
- Error tracking
- Performance metrics

### Render
- Build logs
- Runtime metrics
- Database monitoring

### Supabase
- Database health
- Query performance
- Storage usage

---

## 🛠️ Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check system health
- Respond to alerts

**Weekly:**
- Review performance metrics
- Check database usage
- Update dependencies

**Monthly:**
- Security audit
- Performance optimization
- Backup verification

---

## 🆘 Troubleshooting

**Backend won't start?**
```bash
# Check environment variables
echo $DATABASE_URL

# Check logs on Render dashboard
# Look for database connection errors
```

**API not responding?**
```bash
# Test endpoint directly
curl -v https://your-service.onrender.com/health

# Check Render logs for errors
# Verify DATABASE_URL is correct
```

**Frontend can't connect to backend?**
```bash
# Check VITE_API_URL in Vercel environment
# Verify CORS is properly configured
# Test in browser console:
fetch('https://your-backend.onrender.com/health').then(r => r.json())
```

See: [TROUBLESHOOTING.md](../reference/TROUBLESHOOTING.md) for more solutions

---

## 📚 Additional Resources

- [Vercel Docs](https://vercel.com/docs)
- [Render Docs](https://render.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [React Docs](https://react.dev)

---

**Next Steps:**
1. Follow [DEPLOYMENT-ACTION-PLAN.md](../DEPLOYMENT-ACTION-PLAN.md)
2. Use [PRE-DEPLOYMENT-CHECKLIST.md](PRE-DEPLOYMENT-CHECKLIST.md)
3. Reference [SYSTEM-ARCHITECTURE.md](SYSTEM-ARCHITECTURE.md)

---

*IntelliCross Technical Deployment Guide v1.0*

# 🎯 DEPLOYMENT ACTION PLAN

**Complete Step-by-Step Deployment Guide**

📋 **Estimated Time:** 45 minutes - 1.5 hours  
🎯 **Target:** Production deployment on Vercel + Render + Supabase  
✅ **Prerequisites:** See PRE-DEPLOYMENT-CHECKLIST.md

---

## 📋 Pre-Deployment Requirements

Before starting, ensure you have:

- [ ] GitHub account and repository access
- [ ] Vercel account (free tier available)
- [ ] Render account (free tier available)
- [ ] Supabase account and project created
- [ ] Environment variables ready
- [ ] API keys and secrets prepared
- [ ] Domain name (optional but recommended)

**Check:** [PRE-DEPLOYMENT-CHECKLIST.md](guides/PRE-DEPLOYMENT-CHECKLIST.md) for complete requirements

---

## 🚀 PHASE 1: Prepare Environment Variables (10 minutes)

### Step 1.1: Frontend Environment Setup

1. **Locate config file:**
   ```bash
   cat config/.env.example
   ```

2. **Create `.env` file in project root:**
   ```bash
   cp config/.env.example .env
   ```

3. **Update with your values:**
   ```env
   VITE_API_URL=https://your-backend-url.onrender.com
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_KEY=your-anon-key-here
   VITE_ENVIRONMENT=production
   ```

### Step 1.2: Backend Environment Setup

1. **Create backend `.env` file:**
   ```bash
   cp config/backend-.env.example backend/.env
   ```

2. **Update with your values:**
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   API_KEY=your-secret-api-key
   ENVIRONMENT=production
   ```

3. **Verify no secrets in git:**
   ```bash
   # Add to .gitignore if not already there
   echo ".env" >> .gitignore
   echo "backend/.env" >> .gitignore
   ```

**✅ Phase 1 Complete:** Environment variables prepared

---

## 🔧 PHASE 2: Setup Supabase Database (15 minutes)

### Step 2.1: Create Supabase Project

1. **Go to:** https://supabase.com
2. **Create new project:**
   - Project name: `IntelliCross-Prod`
   - Region: Closest to your users
   - Password: Strong password (save securely)

3. **Wait for initialization** (2-3 minutes)

### Step 2.2: Get Connection Details

1. **In Supabase Dashboard:**
   - Go to `Settings > Database`
   - Copy: `Connection string (URI)`

2. **Format for `.env`:**
   ```env
   DATABASE_URL=postgresql://postgres:PASSWORD@DB_HOST:5432/postgres
   ```

### Step 2.3: Initialize Database Schema

1. **Run migrations:**
   ```bash
   cd backend
   python -m alembic upgrade head
   ```

2. **Verify tables created:**
   ```bash
   # In Supabase dashboard, check Tables section
   ```

**✅ Phase 2 Complete:** Database ready

---

## 📦 PHASE 3: Deploy Backend to Render (15 minutes)

### Step 3.1: Prepare Backend Code

1. **Ensure requirements.txt is complete:**
   ```bash
   cat backend/requirements.txt
   ```

2. **Verify main.py is in backend folder:**
   ```bash
   ls -la backend/main.py
   ```

3. **Check all imports are available:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Step 3.2: Create Render Service

1. **Go to:** https://render.com

2. **Create new Web Service:**
   - Name: `IntelliCross-Backend`
   - Environment: Python
   - Region: US (Oregon) or closest to users
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`

3. **Connect repository:**
   - Select: Your GitHub repository
   - Branch: `main`
   - Auto-deploy: Enable

### Step 3.3: Configure Environment Variables in Render

1. **In Render dashboard:**
   - Go to Environment settings
   - Add each variable from `backend/.env`:

   ```
   DATABASE_URL = postgresql://...
   SUPABASE_URL = https://your-project.supabase.co
   SUPABASE_KEY = your-service-role-key
   API_KEY = your-secret-key
   ENVIRONMENT = production
   ```

2. **Save and deploy**

### Step 3.4: Verify Backend Deployment

1. **Wait for deployment** (2-3 minutes)

2. **Test the API:**
   ```bash
   curl https://your-backend-name.onrender.com/health
   # Should return: {"status": "healthy"}
   ```

3. **Save backend URL:**
   ```
   https://your-backend-name.onrender.com
   ```

**✅ Phase 3 Complete:** Backend deployed

---

## 🎨 PHASE 4: Deploy Frontend to Vercel (10 minutes)

### Step 4.1: Prepare Vercel Configuration

1. **Copy vercel.json:**
   ```bash
   cp config/vercel.json.example vercel.json
   ```

2. **Update with your backend URL:**
   ```json
   {
     "buildCommand": "npm run build",
     "outputDirectory": "dist",
     "env": {
       "VITE_API_URL": "https://your-backend-name.onrender.com"
     }
   }
   ```

### Step 4.2: Deploy to Vercel

1. **Option A: Using Vercel CLI**
   ```bash
   npm install -g vercel
   vercel --prod
   ```

2. **Option B: GitHub Integration (Recommended)**
   - Go to: https://vercel.com
   - Click: Import Project
   - Select: Your GitHub repository
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

### Step 4.3: Add Environment Variables to Vercel

1. **In Vercel Project Settings:**
   - Go to: Environment Variables
   - Add:
     ```
     VITE_API_URL = https://your-backend-name.onrender.com
     VITE_SUPABASE_URL = https://your-project.supabase.co
     VITE_SUPABASE_KEY = your-anon-key
     VITE_ENVIRONMENT = production
     ```

2. **Redeploy** to apply environment variables

### Step 4.4: Verify Frontend Deployment

1. **Open your Vercel URL**
   ```
   https://your-project-name.vercel.app
   ```

2. **Test the interface:**
   - Can you see the main dashboard?
   - Can you see the video feed component?
   - Can any buttons be clicked?

**✅ Phase 4 Complete:** Frontend deployed

---

## 🔗 PHASE 5: Integration & Verification (10 minutes)

### Step 5.1: Test API Integration

1. **Open browser console:**
   ```
   Your Frontend URL/
   ```

2. **Open DevTools (F12) → Console tab**

3. **Test API call:**
   ```javascript
   fetch('https://your-backend-name.onrender.com/api/status')
     .then(r => r.json())
     .then(d => console.log('Status:', d))
   ```

4. **Expected output:**
   ```
   Status: {status: 'operational', version: '1.0.0'}
   ```

### Step 5.2: Test Key Features

- [ ] Video feed loads
- [ ] Detection data displays
- [ ] Alerts show correctly
- [ ] Map displays properly
- [ ] Hospital data loads
- [ ] Emergency panel works

### Step 5.3: Enable SSL/HTTPS

1. **Vercel:** Automatic (free)
2. **Render:** Automatic (free)
3. **Supabase:** Automatic (free)

**Verify:** All URLs start with `https://`

### Step 5.4: Set Up Monitoring

1. **Enable Sentry (Optional but recommended):**
   ```bash
   npm install @sentry/react
   ```

2. **Add to your app:**
   ```typescript
   import * as Sentry from "@sentry/react";
   
   Sentry.init({
     dsn: "your-sentry-dsn",
     environment: "production"
   });
   ```

### Step 5.5: Domain Setup (Optional)

1. **Add custom domain in Vercel:**
   - Settings → Domains
   - Add your custom domain
   - Update DNS records at your registrar

2. **Configure CORS if needed:**
   - Backend `main.py`: Ensure your frontend URL is in CORS origins

**✅ Phase 5 Complete:** System verified and operational

---

## 📊 PHASE 6: Production Checklist (5 minutes)

### Security Verification

- [ ] No secrets in repository
- [ ] All API keys use environment variables
- [ ] CORS is properly configured
- [ ] SSL/HTTPS is enabled everywhere
- [ ] Database backups are enabled
- [ ] Supabase Row Level Security (RLS) is enabled

### Performance Verification

- [ ] Frontend loads in < 3 seconds
- [ ] API endpoints respond in < 500ms
- [ ] Images are optimized
- [ ] No console errors on page load
- [ ] All features responsive on mobile

### Operations Setup

- [ ] Error tracking enabled (Sentry)
- [ ] Logging configured
- [ ] Monitoring dashboards set up
- [ ] Alerts configured for failures
- [ ] Backup schedule confirmed

### Documentation

- [ ] Document your deployed URLs
- [ ] Note all API endpoints used
- [ ] Record all API keys locations
- [ ] Document any custom changes
- [ ] Keep admin contact information

**✅ Phase 6 Complete:** Production ready!

---

## 🎉 DEPLOYMENT COMPLETE

### Summary of Deployed Services

| Service | URL | Status |
|---------|-----|--------|
| Frontend | `https://your-project.vercel.app` | ✅ |
| Backend API | `https://your-backend.onrender.com` | ✅ |
| Database | Supabase PostgreSQL | ✅ |
| Monitoring | Sentry Dashboard | ✅ |

### Your Production URLs

**Frontend:** https://your-project.vercel.app  
**Backend:** https://your-backend.onrender.com  
**Database:** Supabase Console  

---

## 🚨 Post-Deployment

### Immediate Actions (First 24 hours)

1. **Monitor for errors:**
   ```
   Sentry Dashboard → Errors
   ```

2. **Check performance:**
   ```
   Vercel Analytics
   Render Metrics
   ```

3. **Test critical workflows:**
   - User login/signup
   - Detection processing
   - Alert generation
   - API integrations

### Ongoing Operations

**Daily:**
- Monitor error logs
- Check system health
- Respond to user issues

**Weekly:**
- Review performance metrics
- Check backup status
- Update security patches

**Monthly:**
- Review logs and performance
- Optimize based on usage
- Plan improvements

See: [MONITORING-AND-OPERATIONS.md](reference/MONITORING-AND-OPERATIONS.md) for detailed procedures

---

## 📖 Reference Guides

**Need help?** Check these documents:

- **Architecture Questions:** [SYSTEM-ARCHITECTURE.md](guides/SYSTEM-ARCHITECTURE.md)
- **Errors/Issues:** [TROUBLESHOOTING.md](reference/TROUBLESHOOTING.md)
- **API Usage:** [API-DOCUMENTATION.md](reference/API-DOCUMENTATION.md)
- **Security:** [SECURITY-HARDENING.md](reference/SECURITY-HARDENING.md)
- **Operations:** [MONITORING-AND-OPERATIONS.md](reference/MONITORING-AND-OPERATIONS.md)

---

## 💾 Backup Your Configuration

```bash
# Save deployment config
mkdir -p deployment-backup
cp .env deployment-backup/
cp backend/.env deployment-backup/
cp vercel.json deployment-backup/
# Never commit these files!
```

---

## ✅ Verification Commands

```bash
# Frontend health check
curl https://your-project.vercel.app/

# Backend health check
curl https://your-backend.onrender.com/health

# Database connection check
curl https://your-backend.onrender.com/api/health
```

All three should return success responses (200 status code).

---

**🎉 Congratulations! IntelliCross is now in production!**

**Next steps:**
1. Monitor the system
2. Gather user feedback
3. Plan next features
4. Keep security updated

**Questions?** See [README-DEPLOYMENT.md](README-DEPLOYMENT.md) for document navigation.

---

*IntelliCross Deployment - Complete!*

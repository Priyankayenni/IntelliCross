# ⚡ DEPLOYMENT QUICKSTART

**Fast 15-minute deployment reference**

---

## 🚀 In 3 Steps

### 1️⃣ Prepare (5 min)

```bash
# Copy env files
cp config/.env.example .env
cp config/backend-.env.example backend/.env

# Update with your values:
# - VITE_API_URL (your backend URL)
# - Database credentials
# - Supabase keys
# - API keys
```

### 2️⃣ Deploy Backend (5 min)

1. Go to: https://render.com
2. Create Web Service
3. Connect your GitHub repo
4. Set environment variables from `backend/.env`
5. Build: `pip install -r requirements.txt`
6. Start: `uvicorn main:app --host 0.0.0.0 --port 10000`
7. Done! Note your URL

### 3️⃣ Deploy Frontend (5 min)

1. Go to: https://vercel.com
2. Import your GitHub repo
3. Add env variables from `.env`
4. Deploy!

---

## ✅ Verify It Works

```bash
# Test backend
curl https://your-backend.onrender.com/health

# Test frontend - open in browser
https://your-project.vercel.app
```

---

## 🔗 Essential URLs

**Get these values:**

| Item | Where |
|------|-------|
| Backend URL | Render dashboard |
| Frontend URL | Vercel dashboard |
| Database URL | Supabase settings |

**Put in .env files**

---

## ⚙️ Environment Variables

### Frontend (.env)
```env
VITE_API_URL=https://your-backend.onrender.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-anon-key
VITE_ENVIRONMENT=production
```

### Backend (backend/.env)
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
ENVIRONMENT=production
```

---

## 🆘 Common Issues

| Issue | Fix |
|-------|-----|
| Backend won't start | Check DATABASE_URL in .env |
| API calls fail | Update VITE_API_URL in frontend |
| Database errors | Verify DATABASE_URL format |
| Env vars not loading | Redeploy after adding them |

---

## 📚 Need More Details?

- **Full guide:** [DEPLOYMENT-ACTION-PLAN.md](DEPLOYMENT-ACTION-PLAN.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](reference/TROUBLESHOOTING.md)
- **All steps:** [README-DEPLOYMENT.md](README-DEPLOYMENT.md)

---

**Done? Check:** [PRE-DEPLOYMENT-CHECKLIST.md](guides/PRE-DEPLOYMENT-CHECKLIST.md)

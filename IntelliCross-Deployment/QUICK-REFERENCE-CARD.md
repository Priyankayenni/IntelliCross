# 📇 QUICK REFERENCE CARD

**Print this page for quick deployment reference**

---

## 🚀 DEPLOYMENT PHASES

### Phase 1: Env Variables (10 min)
```bash
cp config/.env.example .env
cp config/backend-.env.example backend/.env
# Edit with your values
```

### Phase 2: Supabase (15 min)
- Create project at supabase.com
- Get connection string
- Add to backend/.env as DATABASE_URL

### Phase 3: Backend to Render (15 min)
- Create Web Service at render.com
- Connect GitHub repo
- Set environment variables
- Deploy

### Phase 4: Frontend to Vercel (10 min)
- Import project at vercel.com
- Set environment variables
- Deploy

### Phase 5: Verify (10 min)
- Test backend: `curl backend-url/health`
- Test frontend: Open in browser
- Test API: Check console in DevTools

---

## 🔑 KEY ENVIRONMENT VARIABLES

### Frontend (.env)
```
VITE_API_URL=https://backend-url
VITE_SUPABASE_URL=https://project.supabase.co
VITE_SUPABASE_KEY=anon-key
```

### Backend (backend/.env)
```
DATABASE_URL=postgresql://...
SUPABASE_URL=https://project.supabase.co
SUPABASE_KEY=service-key
```

---

## 🔗 DEPLOYMENT PLATFORMS

| Platform | Link | What |
|----------|------|------|
| Render | render.com | Backend API |
| Vercel | vercel.com | Frontend |
| Supabase | supabase.com | Database |

---

## 📋 PRE-FLIGHT CHECKLIST

- [ ] GitHub repo ready
- [ ] Environment variables prepared
- [ ] Supabase project created
- [ ] Render account ready
- [ ] Vercel account ready
- [ ] API keys secured
- [ ] .gitignore has .env files

---

## ✅ VERIFICATION TESTS

```bash
# Backend health
curl https://backend-url/health
# Should return: {status: healthy}

# Frontend loads
https://frontend-url/
# Should show dashboard

# API works
fetch('https://backend-url/api/status')
# Should return data
```

---

## 🆘 QUICK TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Backend fails | Check DATABASE_URL |
| API not found | Check VITE_API_URL |
| Env vars missing | Redeploy after setting them |
| CORS error | Backend CORS config wrong |
| Database error | Verify connection string |

---

## 📞 DOCUMENTATION LINKS

- Main guide: README-DEPLOYMENT.md
- Step-by-step: DEPLOYMENT-ACTION-PLAN.md
- Troubleshooting: reference/TROUBLESHOOTING.md
- Architecture: guides/SYSTEM-ARCHITECTURE.md
- API docs: reference/API-DOCUMENTATION.md

---

## ⏱️ DEPLOYMENT TIME

| Phase | Time |
|-------|------|
| Setup env | 10 min |
| Supabase | 15 min |
| Backend | 15 min |
| Frontend | 10 min |
| Verify | 10 min |
| **Total** | **~50 min** |

---

## 💾 FILES YOU NEED

From `/config`:
- vercel.json.example
- render.yaml.example (optional)
- .env.example
- backend-.env.example

From `/backend`:
- requirements.txt
- main.py

---

## 🔐 SECURITY REMINDERS

✅ Never commit .env files
✅ Use strong API keys
✅ Enable HTTPS (automatic)
✅ Set database backups
✅ Enable RLS in Supabase
✅ Use environment variables only

---

**Print this card & keep nearby during deployment!**

*For details, see README-DEPLOYMENT.md*

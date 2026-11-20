# 🆘 TROUBLESHOOTING GUIDE

**40+ Solutions for Common Deployment Issues**

---

## 🔴 Deployment & Startup Issues

### Issue: Backend fails to start on Render

**Error Message:**
```
ERROR: Application failed to start
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
1. Check `requirements.txt` exists in backend folder
2. Verify build command: `pip install -r requirements.txt`
3. Check Python version: Must be 3.9+
4. Install locally to verify: `pip install -r requirements.txt`
5. Check requirements.txt syntax (no special characters)
6. Try: Delete all cached requirements in Render environment

**Verification:**
```bash
cd backend
pip install -r requirements.txt
python -c "import fastapi; print('OK')"
```

---

### Issue: Frontend build fails on Vercel

**Error Message:**
```
Build failed: npm ERR! code ERESOLVE
```

**Solutions:**
1. Check Node.js version (16+ required)
2. Delete package-lock.json and retry
3. Update npm: `npm install -g npm@latest`
4. Check for conflicting peer dependencies
5. Use `--legacy-peer-deps` flag if needed
6. Ensure all imports are correct in src/

**Verification:**
```bash
npm install
npm run build
# Should create dist/ folder without errors
```

---

### Issue: Docker build fails

**Error Message:**
```
ERROR: failed to solve with frontend dockerfile.v0
```

**Solutions:**
1. Check Dockerfile syntax
2. Verify base image exists and is public
3. Check for invalid Docker commands
4. Ensure all required files exist
5. Build locally first: `docker build -t test .`
6. Check Docker daemon is running

**Verification:**
```bash
docker build -f docker/Dockerfile -t intellicross-backend .
```

---

## 🔗 Connection & Network Issues

### Issue: Backend API unreachable from frontend

**Error in Browser Console:**
```
Failed to fetch https://your-backend.onrender.com/api/...
```

**Solutions:**
1. **Check backend URL:**
   - Verify `VITE_API_URL` in .env
   - Confirm backend is deployed and running
   - Test with curl: `curl https://your-backend.onrender.com/health`

2. **CORS Issues:**
   - Backend CORS must allow frontend URL
   - Update backend main.py:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend.vercel.app"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
   - Redeploy backend

3. **Network Issues:**
   - Check internet connection
   - Verify firewall isn't blocking
   - Try from different network

**Verification:**
```javascript
// In browser console
fetch('https://your-backend.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log(d))
```

---

### Issue: Database connection fails

**Error Message:**
```
could not connect to server: Connection refused
```

**Solutions:**
1. **Verify DATABASE_URL:**
   - Get from Supabase: Settings > Database > Connection string
   - Format: `postgresql://user:password@host:5432/dbname`
   - Confirm username and password match
   - Test connection string locally

2. **Supabase Issues:**
   - Check if Supabase project is running
   - Verify database isn't suspended
   - Check IP whitelist (should include Render IP)
   - Try resetting the password

3. **Render Configuration:**
   - Ensure DATABASE_URL is in environment variables
   - No typos in variable name
   - Redeploy after changing

**Verification:**
```bash
# Test locally
psql "postgresql://user:password@host:5432/dbname" -c "SELECT 1;"

# Should return: 1
```

---

### Issue: Cannot reach Supabase from backend

**Error:**
```
Connection to Supabase failed
```

**Solutions:**
1. Verify SUPABASE_URL format: `https://xxxxx.supabase.co`
2. Verify SUPABASE_KEY is service role key (not anon key)
3. Check network connectivity
4. Verify credentials in Supabase dashboard
5. Check if API is enabled in Supabase

**Test:**
```python
import os
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)
result = supabase.table("your_table").select("*").limit(1).execute()
print(result)
```

---

## 🔐 Authentication Issues

### Issue: JWT token invalid or expired

**Error:**
```
401 Unauthorized: Invalid token
```

**Solutions:**
1. **Token Expired:**
   - Use refresh token endpoint
   - Re-login to get new token
   - Check token expiration time

2. **Invalid Token:**
   - Ensure token format is correct (Bearer scheme)
   - Check token wasn't corrupted in transit
   - Verify signing key matches

3. **Token Not Sent:**
   - Add Authorization header:
   ```javascript
   headers: {
     'Authorization': `Bearer ${token}`
   }
   ```

**Verification:**
```bash
# Decode JWT at jwt.io
# Verify exp (expiration) date hasn't passed
```

---

### Issue: Login fails with "invalid credentials"

**Error:**
```
401: Invalid credentials
```

**Solutions:**
1. **Wrong Email/Password:**
   - Verify email exists in database
   - Check password is correct
   - Password is case-sensitive

2. **Account Issues:**
   - Check if account is active
   - Verify email is confirmed (if required)
   - Try password reset

3. **Database Issues:**
   - Verify users table exists
   - Check password hashing works
   - Query users table directly

**Verification:**
```bash
# In Supabase dashboard
# Check users table has the user
```

---

### Issue: CORS errors in browser

**Error:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solutions:**
1. **Update Backend CORS:**
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend.vercel.app"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Redeploy Backend**

3. **Check CORS Headers:**
   ```bash
   curl -i https://your-backend.onrender.com/health
   # Look for: Access-Control-Allow-Origin
   ```

**Verification:**
```javascript
// Browser DevTools → Network tab
// Check response headers for CORS headers
```

---

## 📊 Data & Database Issues

### Issue: Database has no data after migration

**Solution:**
1. **Verify migrations ran:**
   ```bash
   cd backend
   python -m alembic current
   # Should show latest migration
   ```

2. **Check migrations exist:**
   ```bash
   ls backend/alembic/versions/
   ```

3. **Run migrations manually:**
   ```bash
   python -m alembic upgrade head
   ```

4. **Verify tables created:**
   - In Supabase dashboard → Tables
   - Should see all tables

---

### Issue: Data not saving to database

**Error:**
```
Insert failed / Update failed
```

**Solutions:**
1. **Check Row Level Security (RLS):**
   - Disable RLS temporarily to test
   - Configure RLS policies properly

2. **Verify Insert Permissions:**
   ```python
   result = supabase.table('table_name').insert(data).execute()
   if result.error:
       print(result.error)
   ```

3. **Check Data Validation:**
   - Ensure data types match schema
   - Check NOT NULL constraints
   - Verify foreign key references exist

---

### Issue: API returns "table not found"

**Error:**
```
ERROR: relation "table_name" does not exist
```

**Solutions:**
1. **Table doesn't exist:**
   - Run migrations: `python -m alembic upgrade head`
   - Check table name spelling (case-sensitive)
   - Verify in Supabase dashboard

2. **Schema issues:**
   - Check if in public schema
   - Verify RLS policies don't hide table

---

## 🎨 Frontend Issues

### Issue: Page shows blank or only shows header

**Solutions:**
1. **Check Console Errors:**
   - Open DevTools (F12) → Console
   - Look for JavaScript errors
   - Check for missing imports

2. **Verify Environment Variables:**
   ```javascript
   console.log(import.meta.env.VITE_API_URL)
   // Should print your API URL
   ```

3. **Check API Calls:**
   - DevTools → Network tab
   - Look for failed requests
   - Check response status codes

4. **React Issues:**
   - Check for console errors
   - Verify component rendering
   - Check state management

---

### Issue: Images not loading

**Solutions:**
1. **Check Image URL:**
   - Verify URL is accessible
   - Check CORS headers if external image

2. **Verify Image Exists:**
   - Open URL in browser
   - Check response status (should be 200)

3. **Check img element:**
   ```html
   <img src={imageUrl} onError={() => console.log('Image failed')} />
   ```

---

### Issue: Styling not applied (Tailwind)

**Solutions:**
1. **Rebuild:**
   ```bash
   npm run build
   ```

2. **Check tailwind.config.js:**
   - Verify src/** is included
   - Check file extensions (tsx, ts)

3. **Clear cache:**
   ```bash
   rm -rf .next node_modules/.cache
   npm run build
   ```

---

## 🚀 Render-Specific Issues

### Issue: "Application failed to start" after deployment

**Solutions:**
1. **Check logs:**
   - Render Dashboard → Logs
   - Look for error messages
   - Check if port 10000 is available

2. **Verify start command:**
   ```
   uvicorn main:app --host 0.0.0.0 --port 10000
   ```

3. **Check environment variables:**
   - All required variables present
   - No typos in names
   - Redeploy after adding variables

---

### Issue: Render service keeps restarting

**Solutions:**
1. **Memory issues:**
   - Upgrade to higher plan
   - Optimize code to use less memory
   - Add monitoring to identify memory leaks

2. **CPU issues:**
   - Optimize slow queries
   - Reduce background jobs
   - Upgrade plan if needed

3. **Check logs for crash reason**

---

## ⚡ Vercel-Specific Issues

### Issue: Frontend deployment keeps failing

**Solutions:**
1. **Check build logs:**
   - Vercel Dashboard → Deployments
   - Look for build errors
   - Fix issues locally first

2. **Clear cache:**
   - Vercel Dashboard → Settings
   - Clear build cache
   - Retry deployment

3. **Check environment variables:**
   - Vercel → Settings → Environment Variables
   - Ensure all variables are set
   - Redeploy after changes

---

### Issue: 404 errors after deployment

**Solutions:**
1. **SPA routing issue:**
   - Add `vercel.json`:
   ```json
   {
     "rewrites": [
       { "source": "/(.*)", "destination": "/index.html" }
     ]
   }
   ```

2. **Rebuild and redeploy**

---

## 🔧 Performance Issues

### Issue: API responses very slow

**Solutions:**
1. **Check database query performance:**
   - Add indexes to frequently queried columns
   - Optimize SQL queries
   - Monitor with Supabase console

2. **Add caching:**
   ```python
   from fastapi import Request
   from fastapi_cache2 import FastAPICache2
   
   @app.get("/api/data")
   @cached(expire=300)
   async def get_data():
       return {"data": "value"}
   ```

3. **Scale up:**
   - Render: Upgrade to higher plan
   - Add Redis for caching

---

### Issue: Frontend loads slowly

**Solutions:**
1. **Check lighthouse score:**
   - DevTools → Lighthouse
   - Look for improvements

2. **Code splitting:**
   - Use React.lazy() for routes
   - Implement dynamic imports

3. **Optimize images:**
   - Compress images
   - Use WebP format
   - Implement lazy loading

---

## 🐛 Debugging Tips

### Enable Verbose Logging

**Backend:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
localStorage.setItem('debug', 'app:*')
```

### Check Environment Variables

**Backend:**
```bash
# On Render, in console:
echo $DATABASE_URL
echo $SUPABASE_URL
```

**Frontend (browser console):**
```javascript
console.log(import.meta.env)
```

### Monitor Real-Time

```bash
# Render logs
curl https://api.render.com/v1/services/{service-id}/logs

# Vercel logs
vercel logs --follow
```

---

## 📞 Getting Help

If you can't find solution here:

1. **Check logs first** - Most clues are in error messages
2. **Search error message** - Often has solutions online
3. **Check official documentation:**
   - [Render Docs](https://render.com/docs)
   - [Vercel Docs](https://vercel.com/docs)
   - [Supabase Docs](https://supabase.com/docs)
   - [FastAPI Docs](https://fastapi.tiangolo.com)

4. **Create minimal reproduction** - Helps identify issue

---

**Still stuck? See [README-DEPLOYMENT.md](../README-DEPLOYMENT.md) for additional resources**

# 🔐 SECURITY HARDENING

**Production Security Best Practices & Hardening Guide**

---

## 🛡️ Defense in Depth Strategy

```
Layer 1: Network Security
   ↓
Layer 2: Application Security
   ↓
Layer 3: Data Security
   ↓
Layer 4: Access Control
```

---

## 🌐 Network Security

### 1. HTTPS/TLS

**Status:**
- ✅ Vercel: Automatic HTTPS
- ✅ Render: Automatic HTTPS
- ✅ Supabase: Automatic HTTPS

**Verification:**
```bash
# Check certificate validity
curl -I https://your-backend.onrender.com
# Should see: SSL certificate verify ok

# Check certificate details
openssl s_client -connect your-backend.onrender.com:443
```

### 2. Security Headers

**Add to Backend (main.py):**
```python
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### 3. CORS Configuration

**Strict CORS Policy:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",  # Production only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight for 10 minutes
)
```

---

## 🔑 Authentication & Authorization

### 1. JWT Token Security

**Token Generation (backend/main.py):**
```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY")  # Must be very strong
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise Exception("Invalid token")
```

**Token Storage (Frontend):**
```typescript
// NEVER store in localStorage (vulnerable to XSS)
// Use httpOnly cookie instead

// Or use sessionStorage for short-lived tokens
sessionStorage.setItem('auth_token', token)

// Clear on logout
sessionStorage.removeItem('auth_token')
```

### 2. Password Security

**Password Hashing (backend/main.py):**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    # bcrypt with cost factor 12 (strong)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Password Requirements:**
```python
def validate_password(password: str):
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain uppercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain digit")
    if not any(char in "!@#$%^&*()" for char in password):
        raise ValueError("Password must contain special character")
    return True
```

### 3. Multi-Factor Authentication (MFA)

**Implementation (Optional but Recommended):**
```python
# Use Supabase built-in MFA
@app.post("/api/auth/enable-mfa")
async def enable_mfa(user_id: str):
    # Use Supabase Auth API
    response = await supabase.auth.admin.user_update_by_id(
        user_id,
        {"user_metadata": {"mfa_enabled": True}}
    )
    return {"status": "MFA enabled"}
```

---

## 💾 Data Security

### 1. Encryption at Rest

**Supabase:**
- ✅ All data encrypted with AES-256
- ✅ Automatic backups encrypted
- No action needed

**Frontend Sensitive Data:**
```typescript
// Use crypto-js for client-side encryption if needed
import CryptoJS from 'crypto-js'

const encrypted = CryptoJS.AES.encrypt(sensitiveData, encryptionKey).toString()
const decrypted = CryptoJS.AES.decrypt(encrypted, encryptionKey).toString(CryptoJS.enc.Utf8)
```

### 2. Encryption in Transit

```
✅ HTTPS/TLS: All data encrypted in transit
✅ Database connection: Encrypted via SSL
✅ API calls: Encrypted by HTTPS
```

### 3. Sensitive Data Handling

**Do NOT log:**
```python
# ❌ BAD
logger.info(f"User password: {password}")

# ✅ GOOD
logger.info("User authentication attempted")
logger.debug(f"User ID: {user_id}")
```

**Mask in Responses:**
```python
# ❌ BAD
return {
    "email": user.email,
    "password_hash": user.password_hash,  # Never expose!
}

# ✅ GOOD
return {
    "user_id": user.id,
    "email": user.email,
    # password_hash never included
}
```

### 4. Database Row Level Security (RLS)

**Enable in Supabase:**
```sql
-- Enable RLS on sensitive tables
ALTER TABLE detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own data
CREATE POLICY "Users see own detections"
ON detections
FOR SELECT
USING (created_by = auth.uid());

-- Create policy: Admins see all data
CREATE POLICY "Admins see all detections"
ON detections
FOR SELECT
USING (
    (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
);
```

---

## 🔒 Access Control

### 1. Role-Based Access Control (RBAC)

**Database Schema:**
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    permissions JSONB
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

**Application Level:**
```python
from enum import Enum
from typing import List

class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

async def has_role(required_role: Role):
    async def role_checker(token: str = Depends(oauth2_scheme)):
        payload = verify_token(token)
        user_role = payload.get("role")
        if user_role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return role_checker

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user = Depends(has_role(Role.ADMIN))):
    # Only admins can delete users
    pass
```

### 2. API Key Management

**Generate Secure Keys:**
```python
import secrets

def generate_api_key():
    return secrets.token_urlsafe(32)

# Format: prefix_random
api_key = f"sk_{generate_api_key()}"
```

**Rotate Keys Regularly:**
```
Monthly API key rotation policy:
1. Generate new key
2. Test with new key
3. Deprecate old key
4. Delete old key after grace period
```

**Key Scoping:**
```python
# Create keys with limited permissions
api_keys = {
    "read_only": ["GET"],
    "limited_write": ["GET", "POST"],
    "full_access": ["GET", "POST", "PUT", "DELETE"]
}
```

---

## 🛡️ Input Validation & Sanitization

### 1. Request Validation

```python
from pydantic import BaseModel, validator, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def password_strong(cls, v):
        if len(v) < 12:
            raise ValueError('Password too weak')
        return v
    
    @validator('full_name')
    def name_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v

@app.post("/api/auth/signup")
async def signup(user: UserCreate):
    # Pydantic automatically validates input
    pass
```

### 2. SQL Injection Prevention

**Use Parameterized Queries:**
```python
# ❌ BAD - Vulnerable to SQL injection
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ GOOD - Safe
query = "SELECT * FROM users WHERE email = $1"
# Use prepared statements with parameters
result = await db.fetch(query, email)
```

### 3. XSS Prevention

**Frontend:**
```typescript
// ❌ BAD - Vulnerable to XSS
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ GOOD - Safe (React automatically escapes)
<div>{userInput}</div>
```

**Backend:**
```python
import html

# Escape HTML in responses
safe_content = html.escape(user_input)
```

---

## 🔄 Secrets Management

### 1. Environment Variables

**Never in code:**
```bash
# ❌ BAD
DATABASE_URL="postgresql://..."
API_KEY="sk_123456789"

# ✅ GOOD - Use environment variables
# Store in .env (local) or platform settings (production)
```

**Vercel Secrets:**
```bash
# Set in Vercel dashboard
Settings > Environment Variables
VITE_API_URL=https://your-backend.onrender.com
```

**Render Secrets:**
```bash
# Set in Render dashboard
Environment > Add Secret
DATABASE_URL=postgresql://...
```

### 2. Secrets Rotation

**Monthly Schedule:**
```
Week 1: Generate new secrets
Week 2: Test with new secrets
Week 3: Rotate old secrets
Week 4: Verify all using new secrets
```

### 3. Secret Scanning

**Setup Git Protection:**
```bash
# Install git hooks
npm install husky pre-commit

# Create hook to scan for secrets
git config --global core.hooksPath ~/.githooks
echo "npm run scan-secrets" > ~/.githooks/pre-commit
```

---

## 🔍 Monitoring & Logging

### 1. Security Logging

```python
import logging
from datetime import datetime

security_logger = logging.getLogger("security")

def log_security_event(event_type: str, user_id: str, details: dict):
    security_logger.warning({
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details,
        "ip_address": request.client.host,
    })

# Log events
log_security_event("login_attempt", user_id, {"success": True})
log_security_event("unauthorized_access", user_id, {"endpoint": "/admin"})
log_security_event("password_reset", user_id, {})
```

### 2. Intrusion Detection

**Monitor for suspicious activity:**
```python
# Failed login attempts
async def monitor_failed_logins(email: str):
    failed_attempts = await get_failed_login_count(email, hours=1)
    if failed_attempts > 5:
        # Lock account or require MFA
        await trigger_security_alert(f"Suspicious login attempts for {email}")

# Unusual API usage
async def monitor_api_usage(user_id: str):
    usage = await get_api_usage_stats(user_id, minutes=5)
    if usage.requests_per_second > 100:
        # Rate limit or investigate
        await trigger_security_alert(f"Unusual API usage by {user_id}")
```

---

## 📋 Security Checklist

### Before Production

- [ ] All secrets in environment variables
- [ ] HTTPS enabled everywhere
- [ ] Security headers configured
- [ ] CORS properly restricted
- [ ] Authentication working
- [ ] Authorization enforced
- [ ] Input validation on all endpoints
- [ ] SQL injection protected
- [ ] XSS protected
- [ ] CSRF tokens if applicable
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Monitoring enabled
- [ ] Backups encrypted
- [ ] Database RLS enabled
- [ ] API keys rotated
- [ ] Dependencies up to date
- [ ] No hardcoded secrets
- [ ] No debug mode enabled
- [ ] Security tests passing

### Ongoing

- [ ] Weekly: Review logs for suspicious activity
- [ ] Monthly: Rotate API keys
- [ ] Monthly: Security scan for vulnerabilities
- [ ] Quarterly: Penetration testing
- [ ] Quarterly: Security training
- [ ] Annually: Full security audit

---

## 🚨 Incident Response

### If Breach Detected

1. **Immediately:**
   - Revoke all active tokens
   - Rotate all API keys
   - Change all passwords
   - Alert all users

2. **Within 1 hour:**
   - Determine scope of breach
   - Enable MFA for all accounts
   - Increase monitoring

3. **Within 24 hours:**
   - Notify affected users
   - File incident report
   - Begin investigation

---

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Security Best Practices](https://cheatsheetseries.owasp.org/)

---

**Next:** See [MONITORING-AND-OPERATIONS.md](MONITORING-AND-OPERATIONS.md) for operational procedures

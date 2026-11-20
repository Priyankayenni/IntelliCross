# 📊 MONITORING AND OPERATIONS

**Production Monitoring Setup & Daily Operations Guide**

---

## 📈 Monitoring Setup

### 1. Error Tracking (Sentry)

**Installation:**
```bash
npm install @sentry/react @sentry/tracing
pip install sentry-sdk
```

**Frontend Setup (src/main.tsx):**
```typescript
import * as Sentry from "@sentry/react"

Sentry.init({
  dsn: "https://your-sentry-dsn@sentry.io/project-id",
  environment: "production",
  tracesSampleRate: 0.1,
  integrations: [
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
})
```

**Backend Setup (backend/main.py):**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    environment="production",
    traces_sample_rate=0.1,
    integrations=[FastApiIntegration()],
)
```

**Monitor:**
- Error dashboard: https://sentry.io/dashboard
- Set up alerts for critical errors
- Review error trends weekly

---

### 2. Performance Monitoring

**Vercel Analytics (Automatic):**
- Frontend performance metrics
- Dashboard: Vercel Project → Analytics
- Key metrics:
  - First Contentful Paint (FCP)
  - Largest Contentful Paint (LCP)
  - Cumulative Layout Shift (CLS)

**Render Metrics:**
- Dashboard: Render Project → Metrics
- CPU usage
- Memory usage
- Network I/O

**Supabase Monitoring:**
- Dashboard: Supabase → Monitoring
- Query performance
- Database size
- Connection count

---

### 3. Uptime Monitoring

**Using StatusPage.io (Optional):**
```bash
# Create free account at statuspage.io
# Add monitors for:
# - Frontend: https://your-frontend.vercel.app
# - Backend: https://your-backend.onrender.com/health
```

**Custom Health Check:**
```python
# In backend main.py
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        await supabase.table("detections").select("*").limit(1).execute()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## 📋 Daily Operations Checklist

### Morning (First Check)

- [ ] Check error tracking (Sentry) for overnight errors
- [ ] Review performance metrics
- [ ] Verify all services are running
- [ ] Check database size and backups
- [ ] Review user reports/feedback

**Commands:**
```bash
# Check services
curl https://your-backend.onrender.com/health
curl https://your-frontend.vercel.app/

# Check database size
# In Supabase: Databases > Storage
```

---

### Throughout the Day

- [ ] Monitor error rates (should be < 0.1%)
- [ ] Watch for performance degradation
- [ ] Respond to user issues
- [ ] Monitor API response times (< 500ms)
- [ ] Track detection processing times

---

### End of Day

- [ ] Review analytics for the day
- [ ] Document any issues encountered
- [ ] Check backup completion
- [ ] Prepare for next day
- [ ] Update on-call roster if needed

---

## 🔔 Alerting Rules

### Critical Alerts (Page On-Call)

| Alert | Threshold | Action |
|-------|-----------|--------|
| Error rate high | > 5% | Check logs, identify cause |
| Backend down | Unreachable | Check Render dashboard |
| Database down | Connection failed | Check Supabase status |
| Memory high | > 90% | Restart or scale up |
| CPU high | > 80% | Identify slow queries |

### Warning Alerts (Email)

| Alert | Threshold |
|-------|-----------|
| Error rate moderate | 1-5% |
| Response time slow | 500ms-1s |
| Memory moderate | 70-90% |
| Database connections high | > 80% |

---

## 📊 Key Metrics to Monitor

### Performance Metrics

```
Backend:
- Request latency (target: < 500ms)
- Database query time (target: < 100ms)
- API throughput (requests/second)
- Error rate (target: < 0.1%)

Frontend:
- Page load time (target: < 3s)
- Time to Interactive (target: < 5s)
- First Contentful Paint (target: < 1.5s)
- Largest Contentful Paint (target: < 2.5s)

Database:
- Query latency (target: < 100ms)
- Connection count
- Database size
- Backup success rate
```

### Business Metrics

```
- Detection count per day
- Alert count per day
- Hospital response time
- User activity
- Feature usage
```

---

## 🔄 Weekly Operations

### Weekly Checklist

- [ ] Review error logs and fix issues
- [ ] Check performance trends
- [ ] Verify backups are working
- [ ] Update dependencies if needed
- [ ] Review database performance
- [ ] Check disk usage
- [ ] Plan any maintenance
- [ ] Review user feedback

### Weekly Report Template

```
Week of: [DATE]

Uptime: [%]
Error Rate: [%]
Avg Response Time: [ms]
Database Size: [GB]
Top Issues:
1. [Issue and resolution]
2. [Issue and resolution]

Planned for next week:
- [Task]
- [Task]
```

---

## 🔧 Database Maintenance

### Daily Backup Verification

```bash
# In Supabase dashboard:
# Backups > Point in Time Recovery
# Should see daily backups
```

### Weekly Tasks

**VACUUM and ANALYZE:**
```sql
-- In Supabase SQL Editor
VACUUM ANALYZE;
```

**Check Index Usage:**
```sql
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename;
```

### Monthly Tasks

**Archive Old Data:**
```sql
-- Archive detections older than 6 months
INSERT INTO detections_archive
SELECT * FROM detections
WHERE created_at < now() - interval '6 months';

DELETE FROM detections
WHERE created_at < now() - interval '6 months';
```

---

## 🛡️ Security Operations

### Daily

- [ ] Monitor authentication logs
- [ ] Check for suspicious API usage
- [ ] Review access logs
- [ ] Monitor failed login attempts

### Weekly

- [ ] Review user permissions
- [ ] Check for unused API keys
- [ ] Verify encryption settings
- [ ] Review firewall rules

### Monthly

- [ ] Rotate API keys
- [ ] Review security patches
- [ ] Audit database access
- [ ] Security assessment

---

## 🚨 Incident Response

### Incident Classification

**Severity 1 (Critical):**
- System completely down
- Data loss
- Security breach
- Response time: Immediate

**Severity 2 (High):**
- Major feature broken
- Severe degradation
- Response time: < 15 min

**Severity 3 (Medium):**
- Minor feature broken
- Moderate degradation
- Response time: < 1 hour

**Severity 4 (Low):**
- Cosmetic issues
- Minor bugs
- Response time: < 24 hours

### Response Procedure

```
1. PAGE ON-CALL (if Severity 1-2)
2. ACKNOWLEDGE issue
3. ASSESS severity
4. ISOLATE problem
5. FIX issue
6. VERIFY solution
7. DOCUMENT incident
8. NOTIFY stakeholders
9. POST-MORTEM (if Severity 1)
```

### Rollback Procedure

```bash
# Backend rollback on Render:
# Dashboard > Deploys > Select previous version > Redeploy

# Frontend rollback on Vercel:
# Dashboard > Deployments > Select previous version > Promote

# Database rollback on Supabase:
# Backups > Point in Time Recovery > Select time
```

---

## 📱 On-Call Procedures

### On-Call Engineer Responsibilities

1. **Availability:** 24/7 monitoring of alerts
2. **Response:** < 15 minutes for P1, < 1 hour for P2
3. **Communication:** Keep team updated
4. **Documentation:** Log all incidents
5. **Escalation:** Page senior engineer if needed

### On-Call Tools

- **Phone Alert:** PagerDuty or Slack integration
- **Dashboard:** Open 24/7 during shift
- **Laptop:** Available for remote access
- **Contacts:** All team members' numbers

### Shift Handoff

```
Outgoing Engineer:
- Summarize status
- Note any ongoing issues
- Transfer contact info

Incoming Engineer:
- Acknowledge receipt
- Review dashboard
- Verify able to respond
```

---

## 📞 Escalation Path

**Level 1 (On-Call):** Try to resolve
**Level 2 (Team Lead):** If Level 1 can't resolve in 30 min
**Level 3 (Engineering Manager):** If Level 2 can't resolve in 1 hour
**Level 4 (CTO):** Critical issues or management decision needed

---

## 🔄 Release Procedures

### Pre-Release

- [ ] Code reviewed and approved
- [ ] All tests passing
- [ ] Staging deployment successful
- [ ] QA sign-off received
- [ ] Rollback plan documented

### Release Steps

```
1. Create release branch
2. Update version numbers
3. Create release notes
4. Tag release in GitHub
5. Deploy to production
6. Monitor for errors
7. Verify features working
8. Communicate with team
```

### Post-Release

- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Document any issues
- [ ] Plan for next release

---

## 📚 Runbooks

### Backend Restart

```bash
# In Render dashboard:
1. Dashboard > Services > Your Service
2. Settings > Restart Service
3. Confirm restart
4. Wait for deployment
5. Verify health check
```

### Database Maintenance

```sql
-- Run weekly
VACUUM ANALYZE;

-- Check for slow queries
SELECT query, mean_time, stddev_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Cache Clear

```python
# Clear Redis cache (if using)
redis_client.flushdb()
```

---

## 📈 Scaling Guidelines

### When to Scale

**Scale Backend when:**
- CPU usage > 80%
- Memory usage > 90%
- Error rate increasing
- Response time > 1 second
- API rate limiting triggered

**Scale Database when:**
- Database size > 80% of limit
- Connection count > 90% of limit
- Query latency increasing
- Backup taking too long

**Scale Frontend when:**
- Build times increasing
- Deployment size > 5MB
- Bandwidth usage high

### Scaling Steps

```bash
# Backend (Render):
1. Dashboard > Plan > Select higher plan
2. Confirm upgrade
3. Service restarts with more resources

# Database (Supabase):
1. Dashboard > Billing > Plan > Upgrade
2. Additional resources available immediately

# Frontend (Vercel):
# Automatic scaling - no action needed
```

---

## 💾 Backup & Recovery

### Daily Backup Verification

```
Check Supabase dashboard:
1. Settings > Backups
2. Verify today's backup exists
3. Note backup size and time
```

### Recovery Procedure

```
1. Identify what went wrong
2. Calculate backup time needed
3. In Supabase: Backups > PITR > Select time
4. Confirm restore
5. Verify data integrity
6. Notify team
7. Document incident
```

---

**Next:** See [SECURITY-HARDENING.md](SECURITY-HARDENING.md) for security procedures

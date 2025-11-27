# Cloud Deployment Guide for Wearable System

## Architecture

```
Internet
   │
   ├─► Frontend (Vercel) ──────┐
   │                            │
   └─► ESP32 (Local) ───────────┼──► Backend (Railway)
                                │      ├─► PostgreSQL (Railway)
                                │      └─► Redis (Railway)
                                │
                                └──► Users' Browsers
```

## 1. Backend Deployment (Railway.app - Recommended)

### Why Railway?
- Free tier available
- Automatic Docker deployment
- Managed PostgreSQL & Redis
- Easy environment variables
- Built-in SSL/HTTPS
- WebSocket support

### Steps:

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository

3. **Add Services**
   ```
   Project Structure:
   ├── Django App (from Dockerfile)
   ├── PostgreSQL (Railway template)
   └── Redis (Railway template)
   ```

4. **Environment Variables** (Railway Dashboard)
   ```bash
   # Django
   SECRET_KEY=your-production-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-app.railway.app,yourdomain.com
   
   # Database (Railway provides automatically)
   POSTGRES_HOST=${{Postgres.RAILWAY_PRIVATE_DOMAIN}}
   POSTGRES_PORT=${{Postgres.RAILWAY_TCP_PROXY_PORT}}
   POSTGRES_USER=${{Postgres.PGUSER}}
   POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
   POSTGRES_DB=${{Postgres.PGDATABASE}}
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   
   # Redis (Railway provides automatically)
   REDIS_URL=${{Redis.REDIS_URL}}
   CELERY_BROKER_URL=${{Redis.REDIS_URL}}
   CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
   
   # CORS
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
   
   # Optional: Monitoring
   SENTRY_DSN=your-sentry-dsn
   ```

5. **Deploy**
   - Railway auto-deploys on git push
   - Get your URL: `https://your-app.railway.app`

### Alternative: Docker Compose on VPS
If you prefer full control, deploy to DigitalOcean, Linode, or AWS EC2:

```bash
# On your VPS
git clone your-repo
cd WearableApi
docker-compose up -d
```

---

## 2. Frontend Deployment (Vercel)

### Steps:

1. **Create Vercel Account**
   - Go to https://vercel.com
   - Sign up with GitHub

2. **Import Project**
   - Click "New Project"
   - Select your frontend repository
   - Framework: Vite

3. **Environment Variables**
   ```bash
   VITE_API_URL=https://your-backend.railway.app/api
   VITE_WS_URL=wss://your-backend.railway.app/ws
   ```

4. **Deploy**
   - Vercel auto-deploys on git push
   - Get your URL: `https://your-frontend.vercel.app`

### Alternative Frontend Hosts:
- **Netlify** (similar to Vercel)
- **AWS Amplify**
- **Cloudflare Pages**

---

## 3. ESP32 Configuration (Update Arduino Code)

The ESP32 stays **local** (in the user's home/clinic) but connects to your **cloud backend**.

### Update `9Bsensors.ino`:

```cpp
// OLD - Local development
const char* baseUrl = "http://192.168.100.6:8000/api";

// NEW - Production cloud
const char* baseUrl = "https://your-backend.railway.app/api";
```

### Add SSL Certificate Handling:

```cpp
#include <WiFiClientSecure.h>

// For HTTPS connections
WiFiClientSecure client;

void setup() {
  // ... existing setup code ...
  
  // Allow insecure HTTPS for now (or add proper certificate)
  client.setInsecure();
}

// Update HTTP requests to use WiFiClientSecure
void sendDataToDjango(...) {
  HTTPClient http;
  http.begin(client, lecturasUrl);  // Use secure client
  // ... rest of code ...
}
```

### Handle Connection Issues:

```cpp
// Add retry logic for unreliable internet
const int MAX_RETRIES = 3;
int retryCount = 0;

while (retryCount < MAX_RETRIES) {
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode == 201) {
    Serial.println("✓ Data sent successfully");
    break;
  } else {
    retryCount++;
    Serial.printf("⚠ Retry %d/%d\n", retryCount, MAX_RETRIES);
    delay(2000);
  }
}
```

---

## 4. Database Migration

### Export Local Data (Optional):

```bash
# On your local machine
docker-compose exec wearable-django python manage.py dumpdata > backup.json
```

### Import to Cloud:

```bash
# On Railway (use Railway CLI or web shell)
railway run python manage.py loaddata backup.json
```

---

## 5. Domain Configuration (Optional)

### Backend Custom Domain:
1. Buy domain (Namecheap, Google Domains, etc.)
2. Add CNAME record: `api.yourdomain.com` → `your-app.railway.app`
3. Update Railway settings to use custom domain
4. Update ESP32 code: `https://api.yourdomain.com/api`

### Frontend Custom Domain:
1. Add domain to Vercel
2. Update DNS records as instructed
3. SSL auto-configured by Vercel

---

## 6. Monitoring & Maintenance

### Logging:
- **Railway**: Built-in logs dashboard
- **Sentry**: Error tracking (already configured)
- **Datadog/New Relic**: Performance monitoring

### Scaling:
- **Railway**: Auto-scales with plan
- **Celery Workers**: Increase worker count in settings
- **Database**: Upgrade plan as needed

### Backups:
```bash
# Automated daily backups
railway run pg_dump > backup-$(date +%Y%m%d).sql
```

---

## 7. Security Checklist

✅ **Django:**
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY`
- [ ] HTTPS only (`SECURE_SSL_REDIRECT=True`)
- [ ] Proper CORS configuration
- [ ] Rate limiting (django-ratelimit)

✅ **Database:**
- [ ] Strong passwords
- [ ] Private network only
- [ ] Regular backups
- [ ] SSL connections

✅ **ESP32:**
- [ ] HTTPS connections
- [ ] No hardcoded credentials
- [ ] Device authentication

✅ **Frontend:**
- [ ] Environment variables for API URLs
- [ ] Content Security Policy
- [ ] HTTPS only

---

## 8. Cost Estimate (Monthly)

### Free Tier (Hobby/Testing):
- **Railway**: $5/month (includes Postgres + Redis + 500 hours)
- **Vercel**: Free (hobby projects)
- **Total**: ~$5/month

### Production (Small Scale):
- **Railway**: $20-50/month (better resources)
- **Vercel**: Free-$20/month
- **Monitoring (Sentry)**: Free tier
- **Total**: ~$20-70/month

### Enterprise Scale:
- **AWS/Azure/GCP**: $200-1000+/month
- Includes: Load balancers, auto-scaling, CDN, advanced monitoring

---

## 9. Deployment Workflow

### Development → Production:

```bash
# 1. Local development
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "Add new feature"

# 2. Test locally
docker-compose up
# Test everything works

# 3. Push to GitHub
git push origin feature/new-feature

# 4. Create Pull Request
# Review code, run CI/CD tests

# 5. Merge to main
# Railway/Vercel auto-deploy to production

# 6. Verify deployment
# Check logs, test endpoints
```

---

## 10. Multiple ESP32 Devices

### Support Multiple Users with ESP32s:

**Option A: One ESP32 per user (physical distribution)**
- Each user has their own ESP32 at home
- All ESP32s connect to same cloud backend
- Each device has unique `device_id` (from MAC address)
- Users log in via web → creates session → ESP32 detects session

**Option B: Clinic/Hospital Setup**
- Multiple ESP32s in one location
- Each station has an ESP32
- Users authenticate at specific stations
- Backend tracks which device for which user

### Code Changes for Multi-Device:
Already implemented! Your current code uses:
```cpp
// Dynamic device ID based on MAC
DEVICE_ID = "ESP32_" + getMacAddress();
```

Backend tracks sessions by:
```python
device_key = f'device_session:{device_id}'
```

---

## Quick Start Commands

### Deploy Backend (Railway):
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Deploy Frontend (Vercel):
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel
```

### Update ESP32:
```cpp
// In 9Bsensors.ino, change:
const char* baseUrl = "https://your-backend.railway.app/api";
// Re-upload to ESP32
```

---

## Troubleshooting

### ESP32 Can't Connect:
1. Check WiFi credentials
2. Verify HTTPS certificate (use `client.setInsecure()` for testing)
3. Check firewall rules
4. Test endpoint with curl: `curl https://your-backend.railway.app/api/device-session/check-session/`

### WebSocket Issues:
1. Ensure WSS (not WS) in production
2. Check ALLOWED_HOSTS includes domain
3. Verify ASGI configuration
4. Test with WebSocket client

### Database Connection Failed:
1. Check DATABASE_URL format
2. Verify SSL settings
3. Check connection limits
4. Review Railway logs

---

## Next Steps

1. **Set up Railway account** and deploy backend
2. **Set up Vercel account** and deploy frontend
3. **Update ESP32 code** with cloud URL
4. **Test end-to-end** with one ESP32
5. **Monitor and optimize** based on usage

---

## Support Resources

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/4.2/howto/deployment/
- **ESP32 HTTPS**: https://randomnerdtutorials.com/esp32-https-requests/

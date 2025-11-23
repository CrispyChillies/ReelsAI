# Render Deployment Guide for ReelsAI

Complete guide to deploying your Django backend and Celery worker on Render.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **External Services Ready**:
   - Supabase database (or use Render PostgreSQL)
   - Redis instance (Upstash, Redis Cloud, or Render Redis)
   - Vector DB (Zilliz/Milvus)

## Option 1: Deploy Using Blueprint (Recommended - Infrastructure as Code)

### Step 1: Configure Redis

Since Render's free tier doesn't include Redis, use a free external Redis provider:

**Option A: Upstash Redis (Free tier available)**
1. Go to [upstash.com](https://upstash.com)
2. Create a new Redis database
3. Choose the region closest to your Render services (Singapore recommended)
4. Copy the `UPSTASH_REDIS_REST_URL` or connection string

**Option B: Redis Cloud (Free 30MB)**
1. Go to [redis.com/try-free](https://redis.com/try-free)
2. Create a database
3. Get your connection string (format: `redis://default:password@host:port`)

### Step 2: Prepare Your Repository

Make sure these files exist in your repository:
- ✅ `render.yaml` (root directory)
- ✅ `backend/build.sh` (build script)
- ✅ `backend/requirements.txt` (updated with gunicorn, redis)
- ✅ `backend/Procfile` (web process)

### Step 3: Deploy via Render Dashboard

1. **Login to Render**: [dashboard.render.com](https://dashboard.render.com)

2. **Create Blueprint**:
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will detect `render.yaml` automatically

3. **Configure Environment Variables**:

   Before deployment, you'll need to set these environment variables:

   **For Web Service (`reelsai-backend`):**
   ```bash
   ALLOWED_HOSTS=reelsai-backend.onrender.com,yourdomain.com
   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://yourdomain.com
   REDIS_URL=redis://default:password@host:port  # From Upstash/Redis Cloud
   
   # Database (if using Supabase)
   DB_NAME=postgres
   DB_USER=postgres.xxxxx
   DB_PASSWORD=your-password
   DB_HOST=aws-0-region.pooler.supabase.com
   DB_PORT=6543
   DB_SSLMODE=require
   
   # Or use Render PostgreSQL
   DATABASE_URL=postgresql://user:pass@host:port/dbname
   
   # External Services
   OPENAI_API_KEY=sk-xxxxx
   GEMINI_API_KEY=xxxxx
   ZILLIZ_URI=https://xxxxx
   ZILLIZ_TOKEN=xxxxx
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=xxxxx
   BSKY_USERNAME=youruser.bsky.social
   BSKY_PASSWORD=yourpassword
   
   # URLs
   FRONTEND_BASE_URL=https://your-frontend.vercel.app
   BACKEND_BASE_URL=https://reelsai-backend.onrender.com
   ```

   **For Worker Service (`reelsai-celery-worker`):**
   Most variables are shared with the web service via the blueprint.

4. **Deploy**:
   - Review the blueprint configuration
   - Click "Apply"
   - Render will create both web and worker services
   - Wait 10-15 minutes for initial build

### Step 4: Verify Deployment

```bash
# Check web service health
curl https://reelsai-backend.onrender.com/

# Test API endpoint
curl https://reelsai-backend.onrender.com/api/

# Check Celery worker logs in Render dashboard
```

---

## Option 2: Manual Deployment (Step by Step)

If you prefer manual setup or want more control:

### Step 1: Create Web Service

1. **New Web Service**:
   - Dashboard → "New" → "Web Service"
   - Connect GitHub repository
   - Select branch: `main`
   - Root Directory: `backend`

2. **Configure Web Service**:
   ```
   Name: reelsai-backend
   Region: Singapore (or closest to your users)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: ./build.sh
   Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 600 reelsai.wsgi:application
   Plan: Starter (or Free)
   ```

3. **Environment Variables**: Add all variables listed in Option 1

4. **Deploy**: Click "Create Web Service"

### Step 2: Create Worker Service

1. **New Background Worker**:
   - Dashboard → "New" → "Background Worker"
   - Connect same repository
   - Select branch: `main`
   - Root Directory: `backend`

2. **Configure Worker**:
   ```
   Name: reelsai-celery-worker
   Region: Singapore (same as web service)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: ./build.sh
   Start Command: celery -A reelsai worker --loglevel=info --concurrency=2
   Plan: Starter
   ```

3. **Environment Variables**: Copy from web service or add manually

4. **Deploy**: Click "Create Background Worker"

---

## Database Setup

### Option A: Use Supabase (Current Setup)

Your `settings.py` already supports Supabase PostgreSQL:
- Keep your current `DB_*` environment variables
- Set `DB_SSLMODE=require`
- Use connection pooler for better performance

### Option B: Use Render PostgreSQL

1. **Create Database**:
   - Dashboard → "New" → "PostgreSQL"
   - Name: `reelsai-db`
   - Plan: Starter (Free)

2. **Update Environment Variables**:
   ```bash
   # Render provides DATABASE_URL automatically
   # Update settings.py to use DATABASE_URL if set
   ```

3. **Update `settings.py`**:
   ```python
   import dj_database_url
   
   # Use DATABASE_URL if available (Render), else use individual vars
   if os.getenv("DATABASE_URL"):
       DATABASES = {
           "default": dj_database_url.config(
               default=os.getenv("DATABASE_URL"),
               conn_max_age=600,
               ssl_require=True
           )
       }
   else:
       # Your existing database configuration
       DATABASES = { ... }
   ```

4. **Install dj-database-url**:
   ```bash
   # Add to requirements.txt
   dj-database-url==2.2.0
   ```

---

## Post-Deployment Configuration

### 1. Set Up Custom Domain (Optional)

1. **In Render**:
   - Go to your web service
   - Settings → Custom Domains
   - Add your domain (e.g., `api.reelsai.com`)

2. **In Your DNS Provider**:
   - Add CNAME record: `api.reelsai.com` → `reelsai-backend.onrender.com`

3. **Update Environment Variables**:
   ```bash
   ALLOWED_HOSTS=reelsai-backend.onrender.com,api.reelsai.com
   BACKEND_BASE_URL=https://api.reelsai.com
   ```

### 2. Enable Auto-Deploy

- Settings → "Auto-Deploy" = Yes
- Now every push to `main` branch will trigger deployment

### 3. Configure Health Checks

Render automatically monitors your service health:
- Default health check path: `/`
- Configure custom path in Settings → Health & Alerts

### 4. Set Up Notifications

- Settings → Notifications
- Add email or Slack webhook for deployment alerts

---

## Managing Celery Tasks

### Create a Celery Task

Example in `apps/feed/tasks.py`:

```python
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_video(self, video_id):
    try:
        logger.info(f"Processing video {video_id}")
        # Your video processing logic
        return {"status": "success", "video_id": video_id}
    except Exception as exc:
        logger.error(f"Error processing video {video_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
```

### Trigger Task from View

```python
from apps.feed.tasks import process_video

# In your view
def create_video(request):
    video = Video.objects.create(...)
    # Trigger async task
    process_video.delay(video.id)
    return Response({"status": "processing"})
```

### Monitor Tasks

1. **View Worker Logs**:
   - Dashboard → `reelsai-celery-worker` → Logs

2. **Check Task Results** (if using django-celery-results):
   ```python
   from django_celery_results.models import TaskResult
   
   # Query recent tasks
   recent_tasks = TaskResult.objects.order_by('-date_created')[:10]
   ```

---

## Scaling Considerations

### Web Service Scaling

**Vertical Scaling** (upgrade instance):
- Free: 512MB RAM, 0.1 CPU
- Starter: 512MB RAM, 0.5 CPU ($7/month)
- Standard: 2GB RAM, 1 CPU ($25/month)
- Pro: 4GB RAM, 2 CPU ($85/month)

**Horizontal Scaling** (multiple instances):
- Upgrade to Standard or higher
- Settings → Scaling → Set number of instances

### Worker Scaling

**For heavy workloads**:
- Increase concurrency: `--concurrency=4`
- Add more worker instances
- Upgrade worker plan for more resources

**Cost Optimization**:
- Use task priorities
- Implement task result expiration
- Set appropriate retry policies

---

## Monitoring & Debugging

### View Logs

**Web Service Logs**:
```bash
# In Render dashboard → Logs
# Or use Render CLI
render logs reelsai-backend --tail
```

**Worker Logs**:
```bash
render logs reelsai-celery-worker --tail
```

### Common Issues

**1. Build Fails**
- Check `build.sh` permissions: `chmod +x build.sh`
- Review build logs for missing dependencies
- Ensure Python version matches: `python --version` in build log

**2. Database Connection Errors**
- Verify `DATABASE_URL` or `DB_*` variables
- Check database is running
- Verify SSL mode settings

**3. Redis Connection Fails**
- Verify `REDIS_URL` format: `redis://user:pass@host:port`
- Test connection in worker logs
- Check Redis provider status

**4. Worker Not Processing Tasks**
- Check worker is running: Dashboard → Worker → Status
- Verify Redis connection in worker logs
- Check task is properly defined with `@shared_task`

**5. Static Files Not Loading**
- Verify `whitenoise` is installed
- Check `collectstatic` ran in build
- Use `STATIC_URL` and `STATIC_ROOT` correctly

### Health Monitoring

**Set Up Alerts**:
1. Dashboard → Service → Settings → Alerts
2. Configure alerts for:
   - Service down
   - High error rate
   - Memory/CPU usage

**External Monitoring**:
- Use UptimeRobot, Pingdom, or StatusCake
- Monitor endpoint: `https://reelsai-backend.onrender.com/health/`

---

## Cost Estimate (Monthly)

### Free Tier (Limitations)
- Web Service (Free): Spins down after 15 min inactivity, 750 hours/month
- Worker: Not available in free tier (use Starter)
- Database: Render Postgres Free (90 days, then $7/month)
- Redis: Use external free tier (Upstash/Redis Cloud)
- **Total**: $0 (with external services)

### Starter Plan (Recommended)
- Web Service (Starter): $7/month - always on, 512MB RAM
- Worker (Starter): $7/month - always on, 512MB RAM
- Redis (Upstash Free): $0
- Database (Supabase Free): $0
- **Total**: $14/month

### Production Plan
- Web Service (Standard): $25/month - 2GB RAM, 1 CPU
- Worker (Standard): $25/month - 2GB RAM, 1 CPU
- Redis (Render): $10/month (or Upstash Pro $30/month)
- Database (Render Postgres): $7/month (or Supabase Pro $25/month)
- **Total**: $67-$87/month

---

## Environment Variables Checklist

Before deploying, ensure you have all these set:

### Required
- [ ] `SECRET_KEY` - Django secret (auto-generated by Render)
- [ ] `ALLOWED_HOSTS` - Your Render domain
- [ ] `DATABASE_URL` or `DB_*` variables
- [ ] `REDIS_URL` - Redis connection string
- [ ] `CORS_ALLOWED_ORIGINS` - Frontend URLs

### External APIs
- [ ] `OPENAI_API_KEY`
- [ ] `GEMINI_API_KEY`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_KEY`
- [ ] `ZILLIZ_URI`
- [ ] `ZILLIZ_TOKEN`

### Optional
- [ ] `BSKY_USERNAME`
- [ ] `BSKY_PASSWORD`
- [ ] `DJANGO_SUPERUSER_USERNAME`
- [ ] `DJANGO_SUPERUSER_EMAIL`
- [ ] `DJANGO_SUPERUSER_PASSWORD`
- [ ] `FRONTEND_BASE_URL`
- [ ] `BACKEND_BASE_URL`

---

## Quick Deploy Commands

### Using Render CLI (Optional)

```bash
# Install Render CLI
npm install -g render

# Login
render login

# Deploy blueprint
render blueprint launch

# View service status
render services list

# View logs
render logs reelsai-backend --tail
```

---

## Production Checklist

Before going live:

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable HTTPS (automatic on Render)
- [ ] Set up proper `CORS_ALLOWED_ORIGINS`
- [ ] Configure database backups
- [ ] Set up monitoring and alerts
- [ ] Test all API endpoints
- [ ] Verify Celery tasks are running
- [ ] Set up custom domain (optional)
- [ ] Configure CDN for static files (optional)
- [ ] Enable auto-deploy
- [ ] Document environment variables
- [ ] Set up error tracking (Sentry)

---

## Troubleshooting Guide

### Service Won't Start

```bash
# Check logs
render logs reelsai-backend

# Common issues:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Build command failed
# 4. Port binding issues (use $PORT)
```

### Database Migration Errors

```bash
# SSH into service (if using Render Shell)
# Or add to build.sh
python manage.py showmigrations
python manage.py migrate --fake-initial
```

### Worker Not Processing

```bash
# Check worker is connected to Redis
render logs reelsai-celery-worker | grep "Connected to redis"

# Test task manually
python manage.py shell
>>> from apps.feed.tasks import process_video
>>> result = process_video.delay(1)
>>> result.status
```

---

## Alternative: Docker Deployment (Advanced)

If you prefer Docker, create `Dockerfile` and deploy as a Docker service:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD gunicorn reelsai.wsgi:application --bind 0.0.0.0:$PORT
```

---

## Support & Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#best-practices)
- [Render Community](https://community.render.com)

---

## Next Steps

1. ✅ Deploy web service
2. ✅ Deploy worker service
3. ✅ Set up Redis
4. ✅ Configure environment variables
5. ✅ Test all endpoints
6. ✅ Monitor logs
7. ✅ Set up custom domain (optional)
8. ✅ Enable auto-deploy
9. ✅ Configure monitoring

**Ready to deploy? Follow Option 1 (Blueprint) for the easiest setup!** 🚀

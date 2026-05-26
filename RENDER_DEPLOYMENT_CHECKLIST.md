# 🚀 Render Deployment Checklist

## Critical Issues to Address Before Deploying to Render

---

## 1️⃣ **CRITICAL: Secret Configuration** ⚠️

### Issue in `conference_ai/settings.py`
```python
# ❌ EXPOSED HARDCODED SECRETS
SECRET_KEY = 'django-insecure-#)6=nb6uyg*+=sb$hvki1juf(-g_3tz#d#7631j446m974ooe+'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ❌ EXPOSED DATABASE PASSWORD
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'networking_ai',
        'USER': 'postgres',
        'PASSWORD': '12345678',  # HARDCODED!
        'HOST': 'localhost',     # LOCAL ONLY
        'PORT': '5432',
    }
}
```

### What to Change
- [ ] Use Django environment variables for all secrets
- [ ] Use `python-decouple` or `python-dotenv` for .env file handling
- [ ] Set `DEBUG = False` in production
- [ ] Use `DATABASE_URL` environment variable
- [ ] Generate secure `SECRET_KEY` for production

### Required .env Variables (don't commit this!)
```bash
# Django
DEBUG=False
SECRET_KEY=<generate new key>
ALLOWED_HOSTS=your-render-url.onrender.com,yourdomain.com

# Database (Render provides this)
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Celery / Redis (Render provides this)
CELERY_BROKER_URL=redis://broker:6379/0
CELERY_RESULT_BACKEND=redis://broker:6379/0

# Optional
FACE_RECOGNITION_MODEL=buffalo_l
FACE_RECOGNITION_SIMILARITY_THRESHOLD=0.6
```

---

## 2️⃣ **Database Connection** 

### Current Issue
```python
# ❌ Hardcoded localhost
'HOST': 'localhost',
```

### What to Change
- [ ] Update `settings.py` to read from `DATABASE_URL` environment variable
- [ ] Use `dj-database-url` package to parse database URL

### Code Example
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        atomic_requests=True,
    )
}
```

### Add to requirements.txt
```
dj-database-url==1.3.0
```

---

## 3️⃣ **Redis/Celery Configuration**

### Current Issue
```python
# ❌ Defaults to localhost
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
```

### What to Change
- [ ] Render will provide a Redis URL via environment variable
- [ ] Update to NOT default to localhost (should fail if not configured)
- [ ] Add Redis URL validation
- [ ] Handle case where Celery is undefined (fall back to CELERY_ALWAYS_EAGER)

### Code Example
```python
# Only set Redis URLs if they're explicitly provided
if os.environ.get('CELERY_BROKER_URL'):
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
else:
    # For Render free tier (no Redis), use synchronous processing
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
```

---

## 4️⃣ **STATIC FILES & MEDIA UPLOADS**

### Current Issues
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

**Problem:** Render has ephemeral filesystem (gets wiped on redeploy)

### What to Change
- [ ] Use S3 or similar object storage for media uploads (selfies, event images)
- [ ] Configure static file serving through Render or S3
- [ ] Install `django-storages` and `boto3` for AWS S3

### Add to requirements.txt
```
django-storages==1.14.2
boto3==1.26.137
```

### Configure S3 in settings.py
```python
# S3 Storage Configuration
if not DEBUG:
    # Static files
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    STATIC_ROOT = 'static/'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # Media files (selfies, event images)
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # AWS credentials (from environment)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_REGION_NAME = 'us-east-1'
else:
    # Local development
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

---

## 5️⃣ **Logging Configuration**

### Current Issue
```python
'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
'filename': os.path.join(BASE_DIR, 'logs', 'celery.log'),
```

**Problem:** Render's ephemeral filesystem means logs are lost on redeploy

### What to Change
- [ ] Use Render's built-in logging (logs output to stdout/stderr)
- [ ] Update logging handlers to use console-based output
- [ ] Remove file-based logging in production

### Code Example
```python
if DEBUG:
    # Development: keep file logging
    LOG_HANDLERS = ['console', 'file']
else:
    # Production on Render: only console logging
    LOG_HANDLERS = ['console']

LOGGING = {
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # ... file handler only in dev
    },
    'loggers': {
        'django': {
            'handlers': LOG_HANDLERS,
            'level': 'INFO',
        },
        # ... rest of loggers use LOG_HANDLERS
    }
}
```

---

## 6️⃣ **SECURITY HEADERS** 🔒

### Add to settings.py
```python
if not DEBUG:
    # HTTPS/SSL
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Header security
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'style-src': ("'self'", "'unsafe-inline'"),
        'script-src': ("'self'",),
    }
```

---

## 7️⃣ **Create render.yaml (Infrastructure as Code)**

### Create file: `render.yaml`
```yaml
services:
  - type: web
    name: conference-ai-api
    env: python
    plan: standard
    buildCommand: pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
    startCommand: gunicorn conference_ai.wsgi:application
    envVars:
      - key: DEBUG
        value: false
      - key: PYTHON_VERSION
        value: 3.11
      - key: SECRET_KEY
        sync: false  # Must generate separately
      - key: DATABASE_URL
        fromDatabase:
          name: conference-ai-db
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          name: conference-ai-redis
          type: redis
          property: connectionString

  - type: redis
    name: conference-ai-redis
    plan: starter
    region: ohio
    ipAllowList: []

  - type: postgres
    name: conference-ai-db
    plan: standard
    region: ohio
    databaseName: networking_ai
    postgresSQLVersion: 15
    ipAllowList: []
```

---

## 8️⃣ **Create Procfile (for Render deployment)**

### Create file: `Procfile`
```
web: gunicorn conference_ai.wsgi:application
worker: celery -A conference_ai worker -l info
```

### Add to requirements.txt
```
gunicorn==21.2.0
```

---

## 9️⃣ **Update requirements.txt**

### Add Missing Production Dependencies
```
# Production server
gunicorn==21.2.0

# Database URL parsing
dj-database-url==1.3.0

# Environment variables
python-decouple==3.8
python-dotenv==1.0.0

# S3 Storage (media uploads)
django-storages==1.14.2
boto3==1.26.137

# CORS (if needed for frontend)
django-cors-headers==4.3.0

# Whitenoise (static file serving)
whitenoise==6.6.0
```

---

## 🔟 **Update settings.py for Production**

### Add these checks at the top
```python
import os
import dj_database_url
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
DEBUG = config('DEBUG', default=True, cast=bool)
ENVIRONMENT = config('ENVIRONMENT', default='development')

# Security
SECRET_KEY = config('SECRET_KEY', default='dev-key-not-secure')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        atomic_requests=True,
    )
}

# Adding static middleware for Render
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... rest of middleware
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 1️⃣1️⃣ **Create .env.example (for documentation)**

### File: `.env.example`
```bash
# Copy this to .env and fill in actual values
# DO NOT COMMIT .env to git!

# Django
DEBUG=False
SECRET_KEY=your-secret-key-here-generate-with-django
ENVIRONMENT=production
ALLOWED_HOSTS=your-domain.onrender.com,www.your-domain.com

# Database (Render provides)
DATABASE_URL=postgres://user:pass@host:5432/dbname

# Redis (Render provides)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 (if using for media storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name

# Optional Settings
FACE_RECOGNITION_MODEL=buffalo_l
FACE_RECOGNITION_SIMILARITY_THRESHOLD=0.6
```

---

## 1️⃣2️⃣ **Add .gitignore entries**

```
# Environment
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# Media files (don't commit user uploads)
media/
staticfiles/

# Database
*.sqlite3
*.db

# Python
__pycache__/
*.pyc
*.pyo
venv/
.venv/
```

---

## 1️⃣3️⃣ **Testing Guide for Render**

### Before deploying, verify:
- [ ] No hardcoded database credentials
- [ ] All secrets in environment variables
- [ ] Static files serve correctly with WhiteNoise
- [ ] Media uploads work with S3
- [ ] Celery tasks process async
- [ ] Logs appear in Render console
- [ ] Database migrations run successfully

### Local testing with Render setup:
```bash
# Copy .env.example to .env and update
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Test locally
python manage.py runserver

# In another terminal, test Celery (if Redis configured)
celery -A conference_ai worker -l info
```

---

## 1️⃣4️⃣ **Render-Specific Configuration**

### Navigate to your Render service dashboard:

1. **Environment** tab → Add variables:
   - `DEBUG=false`
   - `SECRET_KEY=<generate new>`
   - `ALLOWED_HOSTS=<your-domain>`
   - `AWS_ACCESS_KEY_ID=<if using S3>`
   - `AWS_SECRET_ACCESS_KEY=<if using S3>`
   - `AWS_STORAGE_BUCKET_NAME=<if using S3>`

2. **Deploy** tab → Set Build Command:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```

3. **Health Check** → Set to `/health/` or similar

---

## 1️⃣5️⃣ **Database Migration on Render**

### First deployment:
```bash
# Run in Render deploy phase (in render.yaml buildCommand)
python manage.py migrate
python manage.py createsuperuser  # Optional, or do via Django admin

# Collect static files
python manage.py collectstatic --noinput
```

### pgvector extension:
```bash
# Render PostgreSQL will need pgvector installed
# Contact Render support OR create this in a Django migration

# In a migration file:
from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    operations = [
        VectorExtension(),
    ]
```

---

## 📋 QUICK DEPLOYMENT STEPS

1. ✅ Fix all hardcoded secrets in `settings.py`
2. ✅ Add `.env.example` file
3. ✅ Update `requirements.txt` with production packages
4. ✅ Create `Procfile` with gunicorn + celery worker
5. ✅ Create `render.yaml` for infrastructure config
6. ✅ Add S3 configuration for media uploads
7. ✅ Update logging for console output
8. ✅ Add security headers
9. ✅ Test locally with env variables
10. ✅ Push to GitHub
11. ✅ Create service on Render dashboard
12. ✅ Link to GitHub repo
13. ✅ Set environment variables in Render dashboard
14. ✅ Deploy!

---

## 🆘 Render-Specific Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'gunicorn'"
**Solution:** Add `gunicorn==21.2.0` to requirements.txt

### Issue: "Static files not found (404)"
**Solution:** Ensure `python manage.py collectstatic` runs in build command

### Issue: "pgvector not available"
**Solution:** Install pgvector in Render's PostgreSQL (see section 15)

### Issue: "Celery tasks not processing"
**Solution:** 
- Verify Redis is provisioned in render.yaml
- Check Celery logs in Render console
- Ensure CELERY_BROKER_URL is set

### Issue: "Media uploads fail"
**Solution:** Configure AWS S3 OR use Render's native storage (if available)

---

## Resources
- [Render Django Guide](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [RedisLabs for Celery Broker](https://redis.com/)
- [AWS S3 Storage for Django](https://django-storages.readthedocs.io/)

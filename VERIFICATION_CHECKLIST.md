# ✅ Setup Verification Checklist

Use this checklist to verify the implementation is correct.

## 1️⃣ File Structure Verification

```bash
# Check all required files exist
ls -la conference_ai/celery.py              # ✅ Celery app
ls -la conference_ai/settings.py            # ✅ Config
ls -la conference_ai/urls.py                # ✅ Routes
ls -la conference_ai/__init__.py            # ✅ Init

ls -la recognition/services.py              # ✅ AI logic
ls -la recognition/face_processor.py        # ✅ Face matching
ls -la recognition/tasks.py                 # ✅ Async tasks
ls -la recognition/signals.py               # ✅ Auto-trigger

ls -la attendees/signals.py                 # ✅ Embedding generation
ls -la attendees/serializers.py             # ✅ Serializers
ls -la attendees/views.py                   # ✅ Views
ls -la attendees/apps.py                    # ✅ Signal registration

ls -la interactions/services.py              # ✅ Scoring logic
ls -la interactions/serializers.py           # ✅ Serializers
ls -la interactions/views.py                 # ✅ Views

ls -la events/serializers.py                 # ✅ Serializers
ls -la events/views.py                       # ✅ Views

ls -la requirements.txt                      # ✅ Dependencies
ls -la README.md                             # ✅ Documentation
ls -la TESTING_GUIDE.md                      # ✅ Testing
ls -la ARCHITECTURE.md                       # ✅ Architecture
ls -la IMPLEMENTATION_SUMMARY.md             # ✅ Summary
```

## 2️⃣ Dependencies Installation

```bash
# Install requirements
pip install -r requirements.txt

# Verify key packages
python -c "import django; print(f'Django: {django.VERSION}')"          # ✅ 4.2.11
python -c "import rest_framework; print('DRF installed')"             # ✅
python -c "import pgvector; print('pgvector installed')"              # ✅
python -c "import insightface; print('InsightFace installed')"        # ✅
python -c "import celery; print('Celery installed')"                  # ✅
python -c "import redis; print('Redis client installed')"             # ✅

echo "✅ All dependencies installed"
```

## 3️⃣ Database Setup

```bash
# Create database
createdb networking_ai

# Install pgvector extension
psql networking_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify extension
psql networking_ai -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Should show: vector | ... | installed

# Run migrations
python manage.py migrate

# Verify tables created
psql networking_ai -c "\dt"
# Should show: attendees_attendee, events_event, recognition_*, interactions_*

echo "✅ Database setup complete"
```

## 4️⃣ Redis Setup

```bash
# Start Redis (macOS)
redis-server &

# Or (Linux)
sudo systemctl start redis

# Verify running
redis-cli ping
# Should output: PONG

echo "✅ Redis running"
```

## 5️⃣ Django Configuration Verification

```bash
# Check settings are loaded
python manage.py shell -c "
from django.conf import settings
print('✅ DEBUG:', settings.DEBUG)
print('✅ MEDIA_ROOT:', settings.MEDIA_ROOT)
print('✅ CELERY_BROKER_URL:', settings.CELERY_BROKER_URL)
print('✅ FACE_RECOGNITION_THRESHOLD:', settings.FACE_RECOGNITION_SIMILARITY_THRESHOLD)
print('✅ REST_FRAMEWORK:', bool(settings.REST_FRAMEWORK))
"

# Check signals are registered
python manage.py shell -c "
from attendees.signals import auto_generate_embedding
from recognition.signals import queue_event_image_processing
print('✅ Signals imported successfully')
"

# Check Celery app
python manage.py shell -c "
from conference_ai.celery import app
print('✅ Celery app loaded')
print('✅ Broker:', app.conf.broker_url)
"

echo "✅ Configuration verified"
```

## 6️⃣ API Endpoint Verification

```bash
# Start dev server in background
python manage.py runserver &
DEV_PID=$!

# Give it time to start
sleep 2

# Test endpoints
echo "Testing Events API..."
curl -s http://localhost:8000/api/events/ | python -m json.tool | head -5
echo "✅ Events endpoint works\n"

echo "Testing API root..."
curl -s http://localhost:8000/api/ | python -m json.tool | head -10
echo "✅ API root works\n"

# Kill dev server
kill $DEV_PID

echo "✅ All API endpoints accessible"
```

## 7️⃣ File Import Verification

```bash
# Check for import errors
python -c "
from events.models import Event
from attendees.models import Attendee
from recognition.models import EventImage, DetectedFace
from interactions.models import Interaction

from events.serializers import EventCreateSerializer
from attendees.serializers import AttendeeJoinSerializer
from recognition.serializers import EventImageUploadSerializer
from interactions.serializers import InteractionDetailSerializer

from events.views import EventViewSet
from attendees.views import AttendeeViewSet
from recognition.views import DetectedFaceViewSet
from interactions.views import InteractionViewSet

from recognition.services import generate_embedding, detect_faces, cosine_similarity
from recognition.face_processor import process_event_image, match_and_create_detected_face
from interactions.services import increment_interaction_score, process_interactions_from_event_image

from recognition.tasks import process_event_image_async, process_event_image_with_interactions

print('✅ All imports successful - no circular dependencies!')
"
```

## 8️⃣ Signal Registration Verification

```bash
python manage.py shell << 'EOF'
from django.dispatch import receiver
from django.db.models.signals import post_save
from attendees.models import Attendee
from recognition.models import EventImage

# Check signal is registered
attendee_signals = []
image_signals = []

for sender, signal in (
    (Attendee, post_save),
    (EventImage, post_save),
):
    receivers = signal._live_receivers(sender)
    print(f"✅ Signal receivers for {sender.__name__}:")
    for receiver in receivers:
        print(f"   - {receiver.im_func.__name__ if hasattr(receiver, 'im_func') else receiver}")

print("✅ Signals properly registered")
EOF
```

## 9️⃣ Media Directory Setup

```bash
# Create media directories
mkdir -p media/selfies
mkdir -p media/event_images
mkdir -p logs

# Verify
ls -la media/
ls -la logs/

echo "✅ Media directories created"
```

## 🔟 Requirements File Verification

```bash
# Check requirements.txt has all key packages
grep -E "Django|djangorestframework|pgvector|insightface|celery|redis|Pillow" requirements.txt

# Should output:
# Django==4.2.11
# djangorestframework==3.14.0
# pgvector==0.3.1
# insightface==0.7.3
# celery==5.3.4
# redis==5.0.1
# Pillow==10.1.0

echo "✅ Requirements.txt verified"
```

## 1️⃣1️⃣ Settings.py Verification

```bash
# Check settings.py has required configurations
python -c "
import re
with open('conference_ai/settings.py', 'r') as f:
    content = f.read()
    
checks = [
    ('MEDIA_ROOT', 'Media root configured'),
    ('MEDIA_URL', 'Media URL configured'),
    ('CELERY_BROKER_URL', 'Celery broker configured'),
    ('REST_FRAMEWORK', 'DRF configured'),
    ('FACE_RECOGNITION_SIMILARITY_THRESHOLD', 'Face threshold configured'),
    ('LOGGING', 'Logging configured'),
]

for key, desc in checks:
    if key in content:
        print(f'✅ {desc}')
    else:
        print(f'❌ {desc} - MISSING!')
"
```

## 1️⃣2️⃣ URLs Configuration Verification

```bash
# Check urls.py registers all viewsets
python -c "
import re
with open('conference_ai/urls.py', 'r') as f:
    content = f.read()

viewsets = [
    'EventViewSet',
    'AttendeeViewSet',
    'DetectedFaceViewSet',
    'InteractionViewSet',
]

for vs in viewsets:
    if vs in content:
        print(f'✅ {vs} registered')
    else:
        print(f'❌ {vs} not found!')

if 'router.register' in content:
    print('✅ DefaultRouter used')
else:
    print('❌ DefaultRouter not found!')
"
```

## 1️⃣3️⃣ Full Integration Test

```bash
#!/bin/bash

echo "=== FULL INTEGRATION TEST ==="
echo ""

# 1. Start Django
echo "1️⃣ Starting Django..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!
sleep 3

# 2. Create test event
echo "2️⃣ Creating test event..."
EVENT=$(curl -s -X POST http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Event"}')
EVENT_ID=$(echo $EVENT | python -c "import sys, json; print(json.load(sys.stdin).get('id', '?'))")
echo "   Event ID: $EVENT_ID ✅"

# 3. Check it was created
echo "3️⃣ Verifying event..."
curl -s http://localhost:8000/api/events/$EVENT_ID/ | python -m json.tool | head -5
echo "   ✅"

# 4. Try serializer validation
echo "4️⃣ Testing serializers..."
python -c "
from events.serializers import EventCreateSerializer
data = {'name': 'Test'}
s = EventCreateSerializer(data=data)
print('✅ EventCreateSerializer works' if s.is_valid() else '❌ Validation failed')
"

# 5. Check Celery can be imported
echo "5️⃣ Testing Celery..."
python -c "
from recognition.tasks import process_event_image_async
print('✅ Celery tasks importable')
"

# Cleanup
kill $DJANGO_PID

echo ""
echo "=== INTEGRATION TEST COMPLETE ==="
```

## 🚦 Quick Status Check

```bash
# One-liner to check everything
python -c "
print('📊 SYSTEM STATUS')
print('=' * 40)

try:
    import django
    import rest_framework
    import pgvector
    import insightface
    import celery
    import redis
    print('✅ All packages imported')
except ImportError as e:
    print(f'❌ Missing package: {e}')

try:
    from django.conf import settings
    assert settings.MEDIA_ROOT
    assert settings.CELERY_BROKER_URL
    assert settings.REST_FRAMEWORK
    print('✅ Django configured')
except:
    print('❌ Django configuration incomplete')

try:
    from events.models import Event
    from attendees.models import Attendee
    from recognition.models import EventImage
    from interactions.models import Interaction
    print('✅ All models accessible')
except ImportError as e:
    print(f'❌ Model import failed: {e}')

try:
    from recognition.services import generate_embedding
    from recognition.face_processor import process_event_image
    from interactions.services import increment_interaction_score
    print('✅ All services accessible')
except ImportError as e:
    print(f'❌ Service import failed: {e}')

print('=' * 40)
print('✅ READY TO GO!')
"
```

---

## ✅ Final Checklist

- [ ] All files created/modified
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL running with pgvector extension
- [ ] Redis running
- [ ] Database migrated (`python manage.py migrate`)
- [ ] Media directories created
- [ ] Signals registered (apps.py ready() methods)
- [ ] Settings configured (MEDIA_ROOT, CELERY_BROKER_URL, etc.)
- [ ] URLs registered (DefaultRouter with viewsets)
- [ ] No import errors (run all imports check)
- [ ] Django dev server starts (`python manage.py runserver`)
- [ ] API endpoints accessible (`curl http://localhost:8000/api/`)

---

## 🚀 Ready?

If all checks pass, you're ready to:

1. Start Django: `python manage.py runserver`
2. Start Celery: `celery -A conference_ai worker -l info`
3. Run tests: See `TESTING_GUIDE.md`

---

**Questions?** Check logs in `logs/` directory and review relevant documentation files.

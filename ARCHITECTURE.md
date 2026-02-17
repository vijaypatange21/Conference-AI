# 🏗️ Architecture & Code Organization Guide

## Module Dependency Graph

```
HTTP Request
    ↓
urls.py (Router)            [conference_ai/urls.py]
    ↓
views.py (ViewSet)          [events/views.py, attendees/views.py, etc.]
    ↓
serializers.py (Validation) [events/serializers.py, etc.]
    ↓
services.py (Logic)         [recognition/services.py, interactions/services.py]
    ↓
models.py (ORM)             [events/models.py, attendees/models.py, etc.]
    ↓
signals.py (Triggers)       [attendees/signals.py, recognition/signals.py]
    ↓
tasks.py (Celery)           [recognition/tasks.py]
    ↓
Redis/Database
```

---

## 1️⃣ HTTP REQUEST LAYER (urls.py)

**File:** `conference_ai/urls.py`

**Purpose:** Route HTTP requests to viewsets

**Key Code:**
```python
from rest_framework.routers import DefaultRouter
from events.views import EventViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
```

**Why:**
- Automatically generates REST endpoints from viewsets
- Reduces boilerplate
- Self-documenting URL structure

---

## 2️⃣ API VIEW LAYER (views.py)

**Files:** 
- `events/views.py`
- `attendees/views.py`
- `recognition/views.py`
- `interactions/views.py`

**Purpose:** Handle HTTP requests/responses

**Key Pattern:**
```python
class EventViewSet(viewsets.ModelViewSet):
    """Handle /api/events/ endpoints"""
    queryset = Event.objects.all()
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        # HTTP logic here
        # Delegate to services
        event = self.get_object()
        serializer = EventImageUploadSerializer(data=request.data)
        # ...
```

**Why Keep Views Thin:**
- HTTP is implementation detail
- Easier to test services without mocking HTTP
- Can reuse services for celery jobs, management commands, etc.
- Easier to add GraphQL, gRPC later

---

## 3️⃣ SERIALIZATION LAYER (serializers.py)

**Files:**
- `events/serializers.py`
- `attendees/serializers.py`
- `recognition/serializers.py`
- `interactions/serializers.py`

**Purpose:** Validate data + convert between Python ↔ JSON

**Key Pattern:**
```python
class EventImageUploadSerializer(serializers.ModelSerializer):
    event_id = serializers.IntegerField(write_only=True)
    
    def validate_event_id(self, value):
        # Validation happens here
        return value
    
    def create(self, validated_data):
        # Creation logic (after validation)
        event_id = validated_data.pop('event_id')
        event = Event.objects.get(id=event_id)
        return EventImage.objects.create(event=event, ...)
```

**Benefits:**
- Automatic validation
- Type hints → API documentation
- Reusable validation logic
- DRF provides browsable API

---

## 4️⃣ BUSINESS LOGIC LAYER (services.py)

### A) Face Recognition Services

**File:** `recognition/services.py`

**Functions:**
```python
def get_face_model() → FaceAnalysis
    """Lazy-load InsightFace model"""

def generate_embedding(image_path: str) → np.ndarray
    """Generate 512-dim embedding from selfie"""
    
def detect_faces(image_path: str) → List[(embedding, face_info)]
    """Detect all faces in image"""

def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) → float
    """Calculate similarity score (0-1)"""
```

**Why Separate Module:**
- AI logic independent of Django ORM
- Easy to test with numpy arrays
- Can swap models easily
- Clear responsibility

### B) Face Matching Pipeline

**File:** `recognition/face_processor.py`

**Functions:**
```python
def process_event_image(event_image: EventImage) → List[DetectedFace]
    """Main pipeline: detect + match + create records"""

def match_and_create_detected_face(event_image: EventImage, embedding) → DetectedFace
    """Query pgvector, find best match, create record"""

def get_matched_attendees_in_image(event_image) → List[Attendee]
    """Get unique attendees detected in image"""
```

**Why Separate from services.py:**
- Handles ORM operations (services.py doesn't)
- Coordinates pgvector queries
- Creates DetectedFace records
- Clear separation: AI logic vs. pipeline logic

### C) Interaction Scoring

**File:** `interactions/services.py`

**Functions:**
```python
def increment_interaction_score(event, attendee1, attendee2, increment=1) → Interaction
    """Increment score between pair, ensure consistent ordering"""

def process_interactions_from_event_image(event_image) → List[Interaction]
    """For each pair of attendees in image, increment score"""

def get_attendee_connections(attendee, event=None) → List[(Attendee, score)]
    """Get attendee's network sorted by score"""
```

**Why This Design:**
- Always stores pairs as (lower_id, higher_id) → no duplicates
- Atomic transactions → prevents race conditions
- Reusable by views, celery, management commands

---

## 5️⃣ DJANGO SIGNAL LAYER (signals.py)

### A) Attendee Signals

**File:** `attendees/signals.py`

**Signal:**
```python
@receiver(post_save, sender=Attendee)
def auto_generate_embedding(sender, instance, created, update_fields, **kwargs):
    """When Attendee is saved:
    1. Check if selfie exists
    2. Call recognition/services.generate_embedding()
    3. Save embedding to database using update()
    """
```

**Why Signals:**
- Automatic: No manual steps in views
- Consistent: Always fire on save
- Reusable: Works with management commands too
- Loose coupling: Services don't know about signals

**Infinite Loop Prevention:**
```python
# Don't regenerate if embedding exists
if not instance.selfie or instance.embedding:
    return

# Don't regenerate if selfie didn't change
if update_fields is not None and 'selfie' not in update_fields:
    return

# Use .update() to bypass this signal on the update
Attendee.objects.filter(pk=instance.pk).update(embedding=...)
```

### B) Recognition Signals

**File:** `recognition/signals.py`

**Signal:**
```python
@receiver(post_save, sender=EventImage)
def queue_event_image_processing(sender, instance, created, **kwargs):
    """When EventImage uploaded:
    1. Queue async Celery task
    2. Or fallback to sync if Celery not configured
    """
```

**Why Queue Async:**
- Heavy processing (face detection) blocks user
- Return response immediately
- User uploads → response immediately
- Background worker processes

---

## 6️⃣ ASYNC TASK LAYER (tasks.py)

**File:** `recognition/tasks.py`

**Tasks:**
```python
@shared_task(bind=True, max_retries=3)
def process_event_image_async(self, event_image_id: int):
    """
    Retry strategy:
    - Retries up to 3 times
    - Exponential backoff: 4^retry seconds
    - Don't retry ObjectDoesNotExist
    """

@shared_task
def process_event_image_with_interactions(event_image_id):
    """Combined: Face detection + Interaction scoring"""
```

**Why Celery:**
- Async: Non-blocking
- Retryable: Network errors don't lose data
- Monitorable: Check status later
- Scalable: Add workers as needed

---

## 7️⃣ ORM LAYER (models.py)

**Attendee Model:**
```python
class Attendee(models.Model):
    user = OneToOneField(User)
    event = ForeignKey(Event)
    selfie = ImageField()
    embedding = VectorField(dimensions=512)  # pgvector!
```

**DetectedFace Model:**
```python
class DetectedFace(models.Model):
    image = ForeignKey(EventImage)
    embedding = VectorField(dimensions=512)  # Face from photo
    matched_attendee = ForeignKey(Attendee, null=True)
```

**Interaction Model:**
```python
class Interaction(models.Model):
    event = ForeignKey(Event)
    attendee1 = ForeignKey(Attendee)  # Lower ID first
    attendee2 = ForeignKey(Attendee)  # Higher ID second
    score = IntegerField()
    
    class Meta:
        unique_together = ("event", "attendee1", "attendee2")
```

---

## 8️⃣ CELERY APP (celery.py)

**File:** `conference_ai/celery.py`

```python
app = Celery('conference_ai')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()  # Auto-find tasks.py in all apps
```

**Why:**
- Central Celery configuration
- Auto-discovers tasks from apps
- Bridge between Django settings and Celery

**settings.py additions:**
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_TIME_LIMIT = 30 * 60
```

---

## 🔄 Full Request Flow Example

### Scenario: User joins event with selfie

```
1. POST /api/events/join/
   ↓
2. attendees/views.py::AttendeeJoinViewSet.join()
   ↓
3. AttendeeJoinSerializer.create()
   → Creates User
   → Creates Attendee (with selfie)
   ↓
4. Django saves Attendee
   ↓
5. attendees/signals.py::auto_generate_embedding fires
   ↓
6. recognition/services.generate_embedding(selfie_path)
   → Load InsightFace model
   → Detect faces
   → Return 512D embedding
   ↓
7. Update attendee.embedding via Attendee.objects.filter(...).update()
   (uses update() to NOT trigger signal again)
   ↓
8. Return JSON response
   {
     "id": 1,
     "embedding_ready": true,
     ...
   }
```

---

## 🔄 Full Request Flow Example 2

### Scenario: Upload group photo

```
1. POST /api/events/1/upload_image/
   ↓
2. events/views.py::EventViewSet.upload_image()
   ↓
3. EventImageUploadSerializer.create()
   → Creates EventImage
   ↓
4. Django saves EventImage
   ↓
5. recognition/signals.py::queue_event_image_processing fires
   ↓
6. Check if Celery configured
   Yes → Call process_event_image_with_interactions.delay(image_id)
   No → Call synchronously
   ↓
7. Return HTTP response immediately (if async)
   ↓
   ┌─────────────────────────────────────────────┐
   │ Celery Worker (background)                  │
   ├─────────────────────────────────────────────┤
   │ 1. Get EventImage from DB                   │
   │ 2. recognition/face_processor.py:           │
   │    - Detect all faces                       │
   │    - For each face:                         │
   │      - Query pgvector for attendees        │
   │      - Calculate cosine similarity         │
   │      - If score > 0.6: create match        │
   │ 3. interactions/services.py:               │
   │    - For each attendee pair:               │
   │      - increment_interaction_score()       │
   │ 4. Done, log result                        │
   └─────────────────────────────────────────────┘
```

---

## 💡 Design Patterns Used

### 1. Service Layer Pattern
- Views → Services → ORM
- Services test without HTTP
- Services reusable

### 2. Signal Pattern
- Post-save hooks
- Automatic workflows
- Decoupled from views

### 3. Celery Task Pattern
- Async background jobs
- With retry logic
- Monitorable

### 4. Repository Pattern (implicit)
- Models as repositories
- ORM abstracts DB

### 5. Factory Pattern
- get_face_model() lazy-loads once
- Reused across requests

---

## 🎯 Why This Architecture Works

| Goal | Solution | Benefit |
|------|----------|---------|
| Testable | Services separate from HTTP | Mock database, test AI logic |
| Scalable | Celery + Redis | Add workers, process more images |
| Maintainable | Clear module separation | Know where to add features |
| Fast | pgvector native vectors | No external vector DB |
| Reliable | Signals + transactions | Consistent state |
| Flexible | DRF serializers | Easy to add validation |
| Observable | Logging + structured logs | Debug issues |

---

## 📊 Complexity by Layer

```
Layer              Complexity  Testability  Reusability
─────────────────────────────────────────────────────────
URLs               🟢 Low      ⭐⭐⭐      🟢 High
Views              🟡 Medium   ⭐⭐       🟡 Medium
Serializers        🟡 Medium   ⭐⭐       🟢 High
Services           🔴 High     ⭐⭐⭐⭐   🟢 Very High
Signals            🟡 Medium   ⭐⭐       🟡 Medium
Tasks              🟡 Medium   ⭐⭐⭐     🟢 High
ORM/Models         🟢 Low      ⭐⭐⭐      🟢 High
```

---

## 🔧 When to Add Code Where

| Requirement | Where to Add |
|-------------|--------------|
| Validate input | → `serializers.py` |
| Calculate score | → `services.py` |
| Query database | → `services.py` or `views.py` |
| Handle HTTP | → `views.py` |
| Transform JSON | → `serializers.py` |
| Heavy processing | → `tasks.py` (Celery) |
| Auto-trigger | → `signals.py` |
| New model | → `models.py` |
| New endpoint | → `urls.py` + `views.py` |

---

## 🚦 Code Quality Checklist

- [ ] Views are thin (delegate to services)
- [ ] Services have no Django imports (pure logic)
- [ ] Signals have no recursive loops
- [ ] Tasks are idempotent (safe to retry)
- [ ] Serializers validate inputs
- [ ] Models use constraints (unique_together, etc.)
- [ ] Logging is structured
- [ ] Errors are handled gracefully
- [ ] Code is commented (why, not what)
- [ ] Type hints used

---

## 🚀 Next Steps to Extend

### Add Webhook Notifications
```
→ interactions/tasks.py: send_notification_async()
→ settings.py: WEBHOOK_URL
```

### Add Real-time Updates
```
→ Use Django Channels + WebSocket
→ Notify clients when interaction updated
```

### Add More AI Features
```
→ Age/gender detection
→ Emotion recognition
→ Outfit color analysis
→ All in recognition/services.py
```

### Add Authentication
```
→ Add JWT token auth to views
→ attendee_id from token
→ DRF permissions decorator
```

---

**Questions?** Read the inline comments in any file or check TESTING_GUIDE.md

# AI Conference Networking - Testing & Usage Guide

## 📋 Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 14+ with pgvector extension
- Redis (for Celery)
- 2GB+ RAM (for InsightFace model)

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup PostgreSQL
   # Create database
   createdb networking_ai
   
   # Install pgvector extension
   psql networking_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3. Install Redis (macOS)
brew install redis
redis-server  # Start Redis (port 6379)

# 4. Django setup
python manage.py migrate
python manage.py createsuperuser  # Create admin user
```

## 🚀 Running the Application

### Terminal 1: Django Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2: Celery Worker (for async task processing)

**With Redis enabled (recommended for production):**
```bash
celery -A conference_ai worker -l info
```

**For development without Redis (synchronous processing):**
```bash
# Edit settings.py and uncomment:
# CELERY_ALWAYS_EAGER = True
# CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Then just run:
python manage.py runserver
```

### Terminal 3: Celery Beat (optional, for scheduling)
```bash
celery -A conference_ai beat -l info
```

---

## 🧪 Testing the Full Pipeline

### Step 1️⃣: Create an Event

**Endpoint:** `POST /api/events/`

```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Conference 2026"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Tech Conference 2026",
  "code": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-02-16T10:30:00Z"
}
```

💾 **Save the `code` and `id` for next steps**

---

### Step 2️⃣: Join Event with Selfie

**Endpoint:** `POST /api/events/join/`

First, prepare an image file (e.g., `selfie.jpg`):
```bash
# Download a sample face image for testing
wget -O selfie.jpg https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400 \
  -q --show-progress
```

```bash
curl -X POST http://localhost:8000/api/events/join/ \
  -F "event_code=550e8400-e29b-41d4-a716-446655440000" \
  -F "selfie=@selfie.jpg" \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "email=john@example.com"
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "username": "john@example.com",
  "email": "john@example.com",
  "event_id": 1,
  "event_name": "Tech Conference 2026",
  "selfie": "/media/selfies/selfie_abc123.jpg",
  "embedding_ready": false,
  "created_at": "2026-02-16T10:32:00Z"
}
```

⚠️ **Note:** `embedding_ready: false` initially. It becomes `true` after:
1. Django signal triggers embedding generation
2. InsightFace processes the selfie
3. Embedding is saved to pgvector

You can check status by polling:
```bash
curl http://localhost:8000/api/attendees/1/
```

---

### Step 3️⃣: Upload Group Photo to Event

**Endpoint:** `POST /api/events/{event_id}/upload-image/`

First, prepare a group photo:
```bash
# Download a sample group photo (multiple faces)
wget -O group.jpg https://images.unsplash.com/photo-1552664730-d307ca884978?w=800 \
  -q --show-progress
```

```bash
curl -X POST http://localhost:8000/api/events/1/upload_image/ \
  -F "image=@group.jpg"
```

**Response:**
```json
{
  "id": 1,
  "event_id": 1,
  "image": "/media/event_images/group_def456.jpg",
  "uploaded_at": "2026-02-16T10:35:00Z",
  "status": {
    "total_faces": 0,
    "matched_faces": 0,
    "processing": true
  }
}
```

⚠️ **The `status` shows during processing:**
- `processing: true` = Celery task still running
- `total_faces > 0` = Face detection completed
- `matched_faces > 0` = Attendees were matched

**Check progress:**
```bash
# Poll every 2 seconds
curl http://localhost:8000/api/events/1/images/

# Or specific image
curl http://localhost:8000/api/detected-faces/1/
```

---

### Step 4️⃣: View Detected Faces & Matches

**Endpoint:** `GET /api/events/{event_id}/images/`

```bash
curl http://localhost:8000/api/events/1/images/
```

**Response:**
```json
[
  {
    "id": 1,
    "event": 1,
    "image": "/media/event_images/group_def456.jpg",
    "uploaded_at": "2026-02-16T10:35:00Z",
    "detected_faces": [
      {
        "id": 1,
        "image": 1,
        "matched_attendee": {
          "id": 1,
          "user_id": 1,
          "username": "john@example.com",
          "email": "john@example.com",
          "event_id": 1,
          "event_name": "Tech Conference 2026",
          "selfie": "/media/selfies/selfie_abc123.jpg",
          "embedding_ready": true
        },
        "embedding": null  # Embeddings not returned for privacy
      }
    ],
    "matched_attendees": [ ... ]
  }
]
```

---

### Step 5️⃣: View Statistics

**Get face recognition statistics:**

```bash
curl http://localhost:8000/api/detected-faces/stats/
```

**Response:**
```json
{
  "total_faces": 5,
  "total_matched": 4,
  "match_rate": "80.0%",
  "by_event": [
    {
      "event_id": 1,
      "event_name": "Tech Conference 2026",
      "total_faces": 5,
      "matched_faces": 4,
      "match_rate": "80.0%"
    }
  ]
}
```

---

### Step 6️⃣: View Interaction Graph

**When multiple attendees are detected in the same image, their interaction score increases.**

```bash
# Get top connected pairs at the event
curl http://localhost:8000/api/interactions/top-combinations/?event_id=1&limit=10
```

**Response:**
```json
[
  {
    "id": 1,
    "event": 1,
    "attendee1_username": "john@example.com",
    "attendee2_username": "jane@example.com",
    "score": 5  # Appeared together 5 times
  },
  {
    "id": 2,
    "event": 1,
    "attendee1_username": "john@example.com",
    "attendee2_username": "bob@example.com",
    "score": 3
  }
]
```

---

### Step 7️⃣: Get My Connections

**Get the attendee's network:**

```bash
# Replace attendee_id with actual attendee ID
curl "http://localhost:8000/api/interactions/my-connections/?attendee_id=1&event_id=1"
```

**Response:**
```json
{
  "attendee": {
    "id": 1,
    "username": "john@example.com",
    "event": 1
  },
  "connections": [
    {
      "id": 1,
      "event": 1,
      "connected_attendee": {
        "id": 2,
        "user_id": 2,
        "username": "jane@example.com",
        "email": "jane@example.com",
        "event_id": 1,
        "event_name": "Tech Conference 2026",
        "selfie": "/media/selfies/selfie_def456.jpg",
        "embedding_ready": true
      },
      "score": 5
    },
    {
      "id": 2,
      "event": 1,
      "connected_attendee": {
        "id": 3,
        "user_id": 3,
        "username": "bob@example.com",
        "email": "bob@example.com",
        "event_id": 1,
        "event_name": "Tech Conference 2026",
        "selfie": "/media/selfies/selfie_ghi789.jpg",
        "embedding_ready": true
      },
      "score": 3
    }
  ],
  "total_connections": 2
}
```

---

## 📊 End-to-End Testing Scenario

### Complete Flow (15-20 minutes)

```bash
#!/bin/bash

# 1. Create event
EVENT=$(curl -s -X POST http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Summit 2026"}')

EVENT_ID=$(echo $EVENT | jq '.id')
EVENT_CODE=$(echo $EVENT | jq -r '.code')
echo "✅ Created Event: ID=$EVENT_ID, Code=$EVENTCODE"

# 2. Add 3 attendees
for i in 1 2 3; do
  ATTENDEE=$(curl -s -X POST http://localhost:8000/api/events/join/ \
    -F "event_code=$EVENT_CODE" \
    -F "selfie=@sample_face_$i.jpg" \
    -F "first_name=Person" \
    -F "last_name=$i" \
    -F "email=person$i@example.com")
  
  ATTENDEE_ID=$(echo $ATTENDEE | jq '.id')
  echo "✅ Added Attendee $i: ID=$ATTENDEE_ID"
  
  # Wait for embedding to generate
  sleep 5
done

# 3. Upload group photo (containing all attendees)
IMAGE=$(curl -s -X POST http://localhost:8000/api/events/$EVENT_ID/upload_image/ \
  -F "image=@group_photo.jpg")

IMAGE_ID=$(echo $IMAGE | jq '.id')
echo "✅ Uploaded Group Photo: ID=$IMAGE_ID"

# Wait for face detection &  matching
sleep 10

# 4. Check detection results
curl -s http://localhost:8000/api/events/$EVENT_ID/images/ | jq .

# 5. Check interactions
curl -s "http://localhost:8000/api/interactions/top-combinations/?event_id=$EVENT_ID" | jq .

# 6. Check attendee's connections
curl -s "http://localhost:8000/api/interactions/my-connections/?attendee_id=1&event_id=$EVENT_ID" | jq .

echo "✅ Full pipeline test completed!"
```

---

## 🔍 Troubleshooting

### Issue: `embedding_ready: false` stays false
**Solution:** Check signal is running
```bash
# In Django terminal, you should see:
# "Generating embedding for attendee ..."
# "Embedding saved for attendee ..."

# If not:
1. Verify attendees/signals.py has ready() method registered
2. Check selfie file actually uploaded:
   ls -la media/selfies/
3. Check logs:
   tail -f logs/django.log
```

### Issue: Face detection returns 0 faces
**Solution:**
```bash
# Check if image is valid:
file group.jpg  # Should be JPEG or PNG

# InsightFace needs clear face photos (>50px face size)
# Try with a higher resolution image

# Check logs for errors:
tail -f logs/django.log | grep "error\|face\|detect"
```

### Issue: Celery tasks not running
**Solution:**
```bash
# Make sure Redis is running:
redis-cli ping  # Should return PONG

# Check Celery worker terminal for errors
# If no tasks appear:
1. Verify CELERY_BROKER_URL in settings.py
2. Check Celery worker is running (Terminal 2)
3. Enable synchronous mode for testing:
   # Edit settings.py:
   # CELERY_ALWAYS_EAGER = True
```

---

## 📈 Performance Tuning

### Increase Face Detection Speed
```python
# settings.py
# Use faster model (lower accuracy):
FACE_RECOGNITION_MODEL = 'buffalo_s'  # vs 'buffalo_l'

# Use GPU if available:
# In recognition/services.py:
# providers=["CUDAProvider"]  # Requires CUDA + ONNX Runtime GPU
```

### Database Optimization
```sql
-- Create indexes for faster queries
CREATE INDEX idx_attendee_embedding ON attendees_attendee USING ivfflat(embedding);
CREATE INDEX idx_detected_face_attendee ON recognition_detectedface(matched_attendee_id);
CREATE INDEX idx_interaction_pair ON interactions_interaction(attendee1_id, attendee2_id);
```

### Celery Optimization
```python
# settings.py
CELERY_WORKER_CONCURRENCY = 4  # Number of parallel workers
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Process one task at a time
```

---

## 📝 Architecture Summary

```
User Request
    ↓
API View (HTTP)
    ↓
Serializer (Validation + Deserialization)
    ↓
Service Layer (Business Logic)
    ↓
Django ORM + Signals
    ↓
Database + Celery Tasks (Async)
    ↓
AI Models (InsightFace, pgvector)
    ↓
Response → Serializer (Serialization) → JSON
```

### Why This Structure?

| Layer | Why | Benefit |
|-------|-----|---------|
| **Views** | Handle HTTP | Thin, testable, easy to change endpoints |
| **Serializers** | Validation | Data consistency, auto-generated docs |
| **Services** | Business logic | Reusable, testable without HTTP |
| **Signals** | Auto-triggers | No manual prompting, always synced |
| **Celery** | Async | Non-blocking, scalable, retry-able |
| **pgvector** | Native vectors | Fast similarity search, no extra services |

---

## 🎓 Learning Path

1. ✅ **Basic:** Run Django server + POST a selfie
2. ✅ **Intermediate:** Upload group photo + see faces detected
3. ✅ **Advanced:** Analyze interaction graph + connections
4. ✅ **Expert:** Configure Celery, optimize pgvector queries, deploy

---

## 📚 Next Steps

### Production Deployment
- [ ] Switch DEBUG=False
- [ ] Use environment variables (.env file)
- [ ] Configure proper SECRET_KEY
- [ ] Setup Redis Cluster for HA
- [ ] Add rate limiting (DRF throttle)
- [ ] Setup logging aggregation (ELK, Datadog)
- [ ] Monitor Celery (Flower)
- [ ] Use CDN for media files (S3, CloudFront)

### Advanced Features
- [ ] 3D face liveness detection
- [ ] Batch processing optimization
- [ ] Real-time notifications (WebSocket)
- [ ] Export interaction graphs (GraphQL)
- [ ] ML model fine-tuning for your dataset
- [ ] Privacy: Blur faces after processing, delete embeddings

### Testing
- [ ] Unit tests for services
- [ ] Integration tests for APIs
- [ ] Load testing with Locust
- [ ] Security testing (OWASP)

---

**Questions?** Check logs in `/media/vijaipatange/New Volume/conference_ai/logs/`

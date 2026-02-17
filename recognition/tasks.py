"""
recognition/tasks.py

Celery tasks for async face recognition pipeline.

Why separate tasks:
- Can be run async without blocking requests
- Can be retried on failure
- Can be monitored and scheduled
- Decouples HTTP request from heavy processing

Retry strategy:
- Retries failed tasks up to 3 times
- Exponential backoff: 2^retry_count seconds
- Ignores certain exceptions that shouldn't be retried
"""

import logging
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_event_image_async(self, event_image_id: int):
    """
    Async task to detect faces and create matches in event image.
    
    Args:
        event_image_id: EventImage primary key
    
    Retry strategy:
    - Retries up to 3 times on failure
    - Exponential backoff: 4, 16, 64 seconds
    - Doesn't retry on ObjectDoesNotExist
    
    Called by: recognition/signals.py (instead of synchronous processing)
    """
    
    try:
        from recognition.models import EventImage
        from recognition.face_processor import process_event_image
        
        # Fetch from DB
        event_image = EventImage.objects.get(id=event_image_id)
        
        logger.info(f"Starting async face processing for EventImage {event_image_id}")
        
        # Run the face detection pipeline
        process_event_image(event_image)
        
        logger.info(f"Completed face processing for EventImage {event_image_id}")
        
    except ObjectDoesNotExist:
        logger.error(f"EventImage {event_image_id} not found")
        # Don't retry - record doesn't exist
        
    except Exception as exc:
        logger.error(f"Error in process_event_image_async: {exc}", exc_info=True)
        
        # Retry with exponential backoff
        # countdown = 2^retry_count
        retry_count = self.request.retries
        countdown = 4 ** retry_count
        
        logger.info(f"Retrying in {countdown}s (attempt {retry_count + 1})")
        
        raise self.retry(exc=exc, countdown=countdown)


@shared_task
def process_event_image_with_interactions(event_image_id: int):
    """
    Async task that combines face processing + interaction scoring.
    
    This is the complete pipeline in one task.
    
    Args:
        event_image_id: EventImage primary key
    
    Called by: recognition/signals.py (with Celery enabled)
    """
    
    try:
        from recognition.models import EventImage
        from recognition.face_processor import process_event_image
        from interactions.services import process_interactions_from_event_image
        
        event_image = EventImage.objects.get(id=event_image_id)
        
        logger.info(f"Starting complete processing for EventImage {event_image_id}")
        
        # Step 1: Detect faces
        faces_detected = process_event_image(event_image)
        logger.info(f"Detected {len(faces_detected)} faces")
        
        # Step 2: Build interaction graph
        interactions = process_interactions_from_event_image(event_image)
        logger.info(f"Created {len(interactions)} interaction pairs")
        
        logger.info(f"Completed full processing for EventImage {event_image_id}")
        
        return {
            'event_image_id': event_image_id,
            'faces_detected': len(faces_detected),
            'interactions_created': len(interactions)
        }
        
    except ObjectDoesNotExist:
        logger.error(f"EventImage {event_image_id} not found")
        
    except Exception as exc:
        logger.error(f"Error in process_event_image_with_interactions: {exc}", exc_info=True)
        raise

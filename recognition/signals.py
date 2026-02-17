"""
recognition/signals.py

Django signals for recognition pipeline.

Trigger:
- When EventImage is created -> Queue async Celery task
- Celery worker processes face detection + interaction scoring

Async benefits:
- Request returns immediately (fast response)
- Heavy processing happens in background worker
- Can retry on failure
- Can be monitored and logged
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from recognition.models import EventImage

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EventImage)
def queue_event_image_processing(sender, instance, created, **kwargs):
    """
    Queue async processing when event image is uploaded.
    
    If Celery is enabled (CELERY_BROKER_URL configured):
    - Immediately returns to request
    - Task runs asynchronously in worker process
    
    If Celery is disabled (for local dev):
    - Falls back to synchronous processing
    - Keeps it simple for development
    
    This is much better than post_save with synchronous work!
    """
    
    if not created:
        return
    
    try:
        # Check if Celery is configured
        if getattr(settings, 'CELERY_BROKER_URL', None):
            # Use async Celery task
            from recognition.tasks import process_event_image_with_interactions
            
            logger.info(
                f"Queueing async processing for EventImage {instance.id} "
                f"(event={instance.event.id})"
            )
            
            # Queue task - returns immediately
            process_event_image_with_interactions.delay(instance.id)
            
        else:
            # Fallback to synchronous processing for development
            logger.warning(
                "CELERY_BROKER_URL not configured - processing synchronously "
                "(not recommended for production)"
            )
            
            from recognition.face_processor import process_event_image
            from interactions.services import process_interactions_from_event_image
            
            process_event_image(instance)
            process_interactions_from_event_image(instance)
        
    except Exception as e:
        logger.error(f"Error queueing EventImage {instance.id}: {e}", exc_info=True)

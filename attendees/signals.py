"""
attendees/signals.py

Django signals for Attendee model lifecycle events.

Why signals:
- Auto-generate embeddings without cluttering views
- Keeps business logic separate from request handling
- Ensures embedding is always synced with selfie

Infinite loop prevention:
- Check if embedding already exists (don't regenerate)
- Only process if selfie actually changed
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from attendees.models import Attendee
from recognition.services import generate_embedding
import numpy as np

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Attendee)
def auto_generate_embedding(sender, instance, created, update_fields, **kwargs):
    """
    Automatically generate face embedding when attendee selfie is uploaded.
    
    This signal fires AFTER the Attendee is saved to DB.
    
    Args:
        sender: The model class (Attendee)
        instance: The Attendee instance being saved
        created: Boolean, True if new instance
        update_fields: Set of field names that were updated
    
    Why post_save:
    - File must be saved to disk before InsightFace can read it
    - We can gracefully handle failures without blocking the save
    
    Why check update_fields:
    - Prevents unnecessary processing if unrelated fields changed
    - Prevents infinite loops from triggering embedding regeneration
    """
    
    # Skip if no selfie or embedding already exists
    if not instance.selfie or instance.embedding:
        return
    
    # Check if selfie actually changed (if update_fields is provided)
    if update_fields is not None and 'selfie' not in update_fields:
        return
    
    try:
        # Get the full file path
        selfie_path = instance.selfie.path
        
        logger.info(f"Generating embedding for attendee {instance.user.username}")
        
        # Call AI service (returns numpy array or None)
        embedding = generate_embedding(selfie_path)
        
        if embedding is None:
            logger.warning(
                f"Could not detect face for attendee {instance.user.username}. "
                "Selfie may need to be replaced."
            )
            return
        
        # Update the VectorField with the embedding
        # pgvector.django.VectorField expects a list or numpy array
        instance.embedding = embedding.tolist()
        
        # Save WITHOUT triggering this signal again
        # Use update() to bypass post_save signal
        Attendee.objects.filter(pk=instance.pk).update(
            embedding=embedding.tolist()
        )
        
        logger.info(f"Embedding saved for attendee {instance.user.username}")
        
    except FileNotFoundError:
        logger.error(f"Selfie file not found for attendee {instance.user.username}")
        # Don't re-raise - the attendee record should still exist even if embedding fails
    
    except Exception as e:
        logger.error(
            f"Error generating embedding for attendee {instance.user.username}: {e}",
            exc_info=True
        )
        # Graceful degradation: attendee exists without embedding

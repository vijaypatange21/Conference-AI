"""
recognition/face_processor.py

Processing pipeline for event images:
1. Detect all faces in image
2. Query pgvector for similar attendee embeddings
3. Create DetectedFace records with matches

Why separate module:
- Can be called from signals or Celery tasks
- Easy to test independently
- Clear separation: services.py (AI models) vs face_processor.py (pipeline logic)
"""

import logging
from typing import Optional, List
from django.db.models import QuerySet
from recognition.services import detect_faces, cosine_similarity
from recognition.models import DetectedFace, EventImage
from attendees.models import Attendee
from events.models import Event
import numpy as np

logger = logging.getLogger(__name__)

# Similarity threshold: faces with score >= 0.6 are considered matches
SIMILARITY_THRESHOLD = 0.6


def process_event_image(event_image: EventImage) -> List[DetectedFace]:
    """
    Main processing pipeline for an event image.
    
    Steps:
    1. Detect all faces in the image
    2. For each face, find matching attendees in that event
    3. Create DetectedFace records
    
    Args:
        event_image: EventImage instance (must have image file saved)
    
    Returns:
        List of created DetectedFace instances
    
    Why this architecture:
    - Returns DetectedFace objects (not just numpy arrays)
    - Handles batch creation efficiently
    - Allows for further processing (e.g., Interaction scoring)
    """
    
    if not event_image.image:
        logger.warning(f"EventImage {event_image.id} has no image file")
        return []
    
    try:
        image_path = event_image.image.path
        logger.info(f"Processing event image {event_image.id} from event {event_image.event.id}")
        
        # Step 1: Detect all faces and their embeddings
        face_results = detect_faces(image_path)
        
        if not face_results:
            logger.info(f"No faces detected in event image {event_image.id}")
            return []
        
        created_faces = []
        
        # Step 2: For each detected face, find matches and create records
        for embedding, face_info in face_results:
            detected_face = match_and_create_detected_face(
                event_image=event_image,
                embedding=embedding
            )
            
            if detected_face:
                created_faces.append(detected_face)
        
        logger.info(
            f"Created {len(created_faces)} DetectedFace records "
            f"from {len(face_results)} faces in event image {event_image.id}"
        )
        
        return created_faces
        
    except FileNotFoundError:
        logger.error(f"Image file not found for event image {event_image.id}")
        raise
    except Exception as e:
        logger.error(f"Error processing event image {event_image.id}: {e}", exc_info=True)
        raise


def match_and_create_detected_face(
    event_image: EventImage,
    embedding: np.ndarray
) -> Optional[DetectedFace]:
    """
    For a single detected face:
    1. Query attendees of that event using pgvector cosine distance
    2. Find best match (if similarity >= threshold)
    3. Create and return DetectedFace record
    
    Args:
        event_image: The EventImage this face was detected in
        embedding: numpy array of shape (512,)
    
    Returns:
        DetectedFace instance (with matched_attendee set if match found)
    
    pgvector query explanation:
    - CosineDistance computes: 1 - (A·B / ||A|| * ||B||)
    - Lower score = more similar (pgvector convention)
    - Similarity threshold 0.6 = cosine distance <= 0.4
    """
    
    try:
        # Get all attendees for this event
        event_attendees = Attendee.objects.filter(
            event=event_image.event,
            embedding__isnull=False  # Only attendees with embeddings
        )
        
        if not event_attendees.exists():
            logger.info(
                f"No attendees with embeddings found for event {event_image.event.id}"
            )
            # Create DetectedFace without match
            return DetectedFace.objects.create(
                image=event_image,
                embedding=embedding.tolist(),
                matched_attendee=None
            )
        
        # Query database using pgvector cosine distance
        # Order by similarity (ascending cosine distance = highest similarity)
        best_match = None
        best_similarity = 0.0
        
        # Fetch attendees and compute similarity in Python
        # (For proper pgvector distance, use raw SQL or annotate with Distance)
        for attendee in event_attendees:
            if attendee.embedding is None:
                continue
            
            # Convert embedding to numpy array for computation
            attendee_emb = np.array(attendee.embedding)
            similarity = cosine_similarity(embedding, attendee_emb)
            
            logger.debug(
                f"Similarity between detected face and attendee {attendee.user.username}: {similarity:.4f}"
            )
            
            # Track best match
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = attendee
        
        # Check if best match meets threshold
        if best_match and best_similarity >= SIMILARITY_THRESHOLD:
            logger.info(
                f"Face matched to attendee {best_match.user.username} "
                f"(similarity: {best_similarity:.4f})"
            )
            detected_face = DetectedFace.objects.create(
                image=event_image,
                embedding=embedding.tolist(),
                matched_attendee=best_match
            )
        else:
            if best_match:
                logger.info(
                    f"No match found (best similarity: {best_similarity:.4f} < {SIMILARITY_THRESHOLD})"
                )
            else:
                logger.info("No attendees to compare against")
            
            detected_face = DetectedFace.objects.create(
                image=event_image,
                embedding=embedding.tolist(),
                matched_attendee=None
            )
        
        return detected_face
        
    except Exception as e:
        logger.error(f"Error in match_and_create_detected_face: {e}", exc_info=True)
        # Still create the DetectedFace record without a match
        return DetectedFace.objects.create(
            image=event_image,
            embedding=embedding.tolist(),
            matched_attendee=None
        )


def get_matched_attendees_in_image(event_image: EventImage) -> List[Attendee]:
    """
    Get list of attendees that were matched in this event image.
    
    Used by: Interaction scoring logic
    """
    return list(
        Attendee.objects.filter(
            detectedface__image=event_image,
            detectedface__matched_attendee__isnull=False
        ).distinct()
    )

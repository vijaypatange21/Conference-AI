"""
interactions/services.py

Builds and maintains the interaction graph.

When multiple attendees are detected in the same image:
- Increment interaction scores for every pair
- Creates or updates Interaction records

Design decisions:
- Always store pairs in consistent order (attendee1 < attendee2 by ID)
  to avoid duplicate records for (A,B) and (B,A)
- Use get_or_create + update for atomic scoring
- Separate service from signal handlers for testability
"""

import logging
from typing import List, Set, Tuple
from django.db import transaction
from itertools import combinations
from attendees.models import Attendee
from events.models import Event
from interactions.models import Interaction
from recognition.models import EventImage

logger = logging.getLogger(__name__)


def increment_interaction_score(
    event: Event,
    attendee1: Attendee,
    attendee2: Attendee,
    score_increment: int = 1
) -> Interaction:
    """
    Increment interaction score between two attendees.
    
    Always stores with attendee1.id < attendee2.id to maintain consistency.
    
    Args:
        event: Event instance
        attendee1, attendee2: Attendee instances
        score_increment: Amount to increment (default: 1)
    
    Returns:
        Updated Interaction instance
    
    Why consistent ordering:
    - Prevents duplicate records (A,B) vs (B,A)
    - Simplifies queries: only query one direction
    - Enforces unique_together constraint
    
    Why use transaction:
    - Ensures atomic read-modify-write
    - Prevents race conditions in multi-worker environments
    """
    
    # Ensure consistent ordering
    if attendee1.id > attendee2.id:
        attendee1, attendee2 = attendee2, attendee1
    
    try:
        with transaction.atomic():
            # Get or create interaction record
            interaction, created = Interaction.objects.get_or_create(
                event=event,
                attendee1=attendee1,
                attendee2=attendee2,
                defaults={'score': 0}
            )
            
            # Increment score
            interaction.score += score_increment
            interaction.save(update_fields=['score'])
            
            action = "Created" if created else "Updated"
            logger.debug(
                f"{action} interaction between {attendee1.user.username} "
                f"and {attendee2.user.username}: score = {interaction.score}"
            )
            
            return interaction
            
    except Exception as e:
        logger.error(
            f"Error incrementing interaction between {attendee1.id} and {attendee2.id}: {e}",
            exc_info=True
        )
        raise


def process_interactions_from_event_image(event_image: EventImage) -> List[Interaction]:
    """
    Process all attendee pairs detected in an event image.
    
    Pipeline:
    1. Get all matched attendees in this image
    2. Generate all unique pairs
    3. Increment score for each pair
    
    Args:
        event_image: EventImage instance
    
    Returns:
        List of Interaction records that were updated/created
    
    Used by: recognition/signals.py (after face detection)
    """
    
    try:
        # Get all attendees matched in this image
        matched_attendees = get_matched_attendees_in_image(event_image)
        
        if len(matched_attendees) < 2:
            logger.debug(
                f"Fewer than 2 matched attendees in image {event_image.id}, "
                "no interactions to process"
            )
            return []
        
        logger.info(
            f"Processing {len(matched_attendees)} attendees from EventImage {event_image.id}"
        )
        
        interactions = []
        
        # Generate all unique pairs: (A, B), (A, C), (B, C), etc.
        for attendee1, attendee2 in combinations(matched_attendees, 2):
            try:
                interaction = increment_interaction_score(
                    event=event_image.event,
                    attendee1=attendee1,
                    attendee2=attendee2,
                    score_increment=1
                )
                interactions.append(interaction)
                
            except Exception as e:
                logger.error(
                    f"Error processing pair ({attendee1.id}, {attendee2.id}): {e}",
                    exc_info=True
                )
                # Continue processing other pairs even if one fails
                continue
        
        logger.info(
            f"Processed {len(interactions)} interaction pairs from EventImage {event_image.id}"
        )
        
        return interactions
        
    except Exception as e:
        logger.error(f"Error in process_interactions_from_event_image: {e}", exc_info=True)
        raise


def get_matched_attendees_in_image(event_image: EventImage) -> List[Attendee]:
    """
    Get list of unique attendees that were matched in this event image.
    
    Queries DetectedFace records where matched_attendee is not null.
    Deduplicates in case an attendee appears multiple times in the image.
    """
    return list(
        Attendee.objects.filter(
            detectedface__image=event_image,
            detectedface__matched_attendee__isnull=False
        ).distinct()
    )


def get_attendee_connections(attendee: Attendee, event: Event = None) -> List[Tuple[Attendee, int]]:
    """
    Get all attendee connections for a given attendee.
    
    Args:
        attendee: Attendee instance
        event: Optional Event filter (if None, returns all connections across events)
    
    Returns:
        List of (connected_attendee, interaction_score) tuples, sorted by score descending
    
    Used by: API endpoint for "my connections"
    """
    
    # Query interactions where this attendee is in either position
    query = Interaction.objects.filter(
        models.Q(attendee1=attendee) | models.Q(attendee2=attendee)
    ).select_related('attendee1', 'attendee2', 'event')
    
    if event:
        query = query.filter(event=event)
    
    connections = []
    for interaction in query:
        # Get the other attendee
        other_attendee = (
            interaction.attendee2
            if interaction.attendee1 == attendee
            else interaction.attendee1
        )
        connections.append((other_attendee, interaction.score))
    
    # Sort by score descending (strongest connections first)
    connections.sort(key=lambda x: x[1], reverse=True)
    
    return connections


# Import here to avoid circular imports
from django.db import models

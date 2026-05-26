"""
interactions/views.py

REST API views for interaction graph.

Endpoints:
- GET /interactions/my_connections -> Get attendee's network (requires attendee_id param)
- GET /interactions?event_id=1 -> List all interactions in event
- GET /interactions/{id} -> Interaction details
- GET /interactions/top_combinations -> Get top interaction pairs
"""

from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from interactions.models import Interaction
from interactions.serializers import (
    InteractionDetailSerializer,
    InteractionListSerializer
)
from attendees.models import Attendee
from events.models import Event


class InteractionViewSet(viewsets.ModelViewSet):
    """
    Interaction scoring and attendee connections.
    
    GET    /interactions              -> List all interactions
    GET    /interactions/{id}         -> Interaction details
    GET    /interactions/my_connections -> Get my connections (requires attendee_id param)
    GET    /interactions/top_combinations -> Get strongest pairs (requires event_id param)
    """
    
    queryset = Interaction.objects.select_related(
        'attendee1', 'attendee2', 'event'
    ).order_by('-score')
    
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == 'my_connections':
            return InteractionDetailSerializer
        return InteractionListSerializer
    
    def get_queryset(self):
        """Filter interactions by event if provided."""
        queryset = super().get_queryset()
        
        event_id = self.request.query_params.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def my_connections(self, request):
        """
        Get network connections for an attendee.
        
        GET /interactions/my_connections?attendee_id=1&event_id=1
        
        Query params:
        - attendee_id: Attendee ID (required)
        - event_id: Optional, limit to event
        
        Returns: List of connected attendees sorted by interaction score
        """
        
        attendee_id = request.query_params.get('attendee_id')
        event_id = request.query_params.get('event_id')
        
        if not attendee_id:
            return Response(
                {'error': 'attendee_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            attendee = Attendee.objects.get(id=attendee_id)
        except Attendee.DoesNotExist:
            return Response(
                {'error': 'Attendee not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get interactions for this attendee
        interactions = Interaction.objects.filter(
            Q(attendee1=attendee) | Q(attendee2=attendee)
        ).select_related('attendee1', 'attendee2', 'event')
        
        if event_id:
            interactions = interactions.filter(event_id=event_id)
        
        # Sort by score descending
        interactions = interactions.order_by('-score')
        
        # Add context so serializer can access current attendee
        request.current_attendee = attendee
        
        serializer = InteractionDetailSerializer(
            interactions,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'attendee': {
                'id': attendee.id,
                'username': attendee.user.username,
                'event': attendee.event.id,
                'event_name': attendee.event.name
            },
            'connections': serializer.data,
            'total_connections': len(serializer.data)
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def discovery_panel(self, request):
        """
        Dashboard discovery feed for the authenticated attendee.

        GET /interactions/discovery_panel?username=jane_doe&event_id=1

        Returns connected attendees sorted by interaction score, with the
        highest-scoring connections first.
        """

        username = request.query_params.get('username')
        event_id = request.query_params.get('event_id')

        if not username:
            return Response(
                {'error': 'username parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            attendee = Attendee.objects.select_related('user', 'event').get(user__username=username)
        except Attendee.DoesNotExist:
            return Response(
                {'error': 'Attendee not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        interactions = Interaction.objects.filter(
            Q(attendee1=attendee) | Q(attendee2=attendee)
        ).select_related('attendee1', 'attendee2', 'event')

        if event_id:
            interactions = interactions.filter(event_id=event_id)

        interactions = interactions.order_by('-score', '-id')

        request.current_attendee = attendee
        serializer = InteractionDetailSerializer(
            interactions,
            many=True,
            context={'request': request}
        )

        return Response({
            'attendee': {
                'id': attendee.id,
                'user_id': attendee.user.id,
                'username': attendee.user.username,
                'event': attendee.event.id,
                'event_name': attendee.event.name,
            },
            'discovery': serializer.data,
            'total_connections': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def top_combinations(self, request):
        """
        Get the strongest attendee pairs (highest interaction scores).
        
        GET /interactions/top_combinations?event_id=1&limit=10
        
        Query params:
        - event_id: Optional, limit to event
        - limit: How many to return (default: 10, max: 100)
        
        Used for: Finding "power couples" at the event
        """
        
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 100)  # Cap at 100
        
        interactions = Interaction.objects.select_related('attendee1', 'attendee2', 'event')
        
        event_id = request.query_params.get('event_id')
        if event_id:
            interactions = interactions.filter(event_id=event_id)
        
        # Order by score and limit
        interactions = interactions.order_by('-score')[:limit]
        
        serializer = InteractionListSerializer(interactions, many=True)
        return Response(serializer.data)

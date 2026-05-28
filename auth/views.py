from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendees.models import Attendee


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        attendee = get_object_or_404(
            Attendee.objects.select_related('user', 'event'),
            user=request.user,
        )

        return Response(
            {
                'id': request.user.id,
                'username': request.user.username,
                'attendee_id': attendee.id,
                'event_id': attendee.event_id,
                'event_name': attendee.event.name,
            }
        )

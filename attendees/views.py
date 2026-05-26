# attendees/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from attendees.models import Attendee
from attendees.serializers import (
    AttendeeJoinSerializer,
    AttendeeDetailSerializer,
    AttendeeSelfieUploadSerializer
)


class AttendeeJoinViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def join(self, request):

        serializer = AttendeeJoinSerializer(
            data=request.data
        )

        if serializer.is_valid():

            attendee = serializer.save()

            response_serializer = (
                AttendeeDetailSerializer(attendee)
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AttendeeViewSet(viewsets.ModelViewSet):

    queryset = (
        Attendee.objects
        .select_related('user', 'event')
    )

    serializer_class = AttendeeDetailSerializer
    permission_classes = [AllowAny]

    # =====================================
    # TEMP DUMMY DATA
    # =====================================

    dummy_data = {
        "id": 1,
        "first_name": "Vijay",
        "last_name": "Patange",
        "email": "vijay@example.com",
        "location": "San Francisco, CA",
        "role": "Senior AI Engineer",
        "website": "https://conferenceai.com",
        "event": {
            "id": 1,
            "name": "AI Summit 2026"
        },
        "selfie": "http://127.0.0.1:8000/media/selfies/selfie.jpeg",
        "created_at": "2026-05-26T10:00:00Z"
    }

    # =====================================
    # GET /api/attendees/{id}/
    # =====================================

    def retrieve(self, request, pk=None):

        return Response(
            self.dummy_data,
            status=status.HTTP_200_OK
        )

    # =====================================
    # PATCH /api/attendees/{id}/update_selfie/
    # =====================================

    @action(detail=True, methods=['patch'])
    def update_selfie(self, request, pk=None):

        return Response(
            self.dummy_data,
            status=status.HTTP_200_OK
        )
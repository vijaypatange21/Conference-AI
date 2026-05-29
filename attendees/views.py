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
import traceback

# =====================================================
# JOIN EVENT
# =====================================================

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


# =====================================================
# ATTENDEE CRUD
# =====================================================

class AttendeeViewSet(viewsets.ModelViewSet):

    queryset = (
        Attendee.objects
        .select_related('user', 'event')
        .all()
    )

    serializer_class = AttendeeDetailSerializer
    permission_classes = [AllowAny]

    # =====================================
    # GET /api/attendees/
    # =====================================

    def list(self, request):

        attendees = self.get_queryset()

        serializer = self.get_serializer(
            attendees,
            many=True
        )

        return Response(serializer.data)

    # =====================================
    # GET /api/attendees/{id}/
    # =====================================

    def retrieve(self, request, pk=None):

        attendee = self.get_object()

        serializer = self.get_serializer(
            attendee
        )

        return Response(serializer.data)

    # =====================================
    # PATCH /api/attendees/{id}/update_selfie/
    # =====================================

    @action(detail=True, methods=['patch'])
    def update_selfie(self, request, pk=None):

        attendee = self.get_object()

        serializer = AttendeeSelfieUploadSerializer(
            attendee,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            try:
                serializer.save()

                response_serializer = AttendeeDetailSerializer(attendee)

                return Response(
                    response_serializer.data,
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                traceback.print_exc()

                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
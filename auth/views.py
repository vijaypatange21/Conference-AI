from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendees.models import Attendee


# ---------------------------------------------------------------------------
# Registration serializer (kept inline — no attendee/event required)
# ---------------------------------------------------------------------------
class RegisterSerializer(serializers.Serializer):
    """Create a bare Django User.  Attendee + event join happens separately."""
    username   = serializers.CharField(max_length=150)
    password   = serializers.CharField(write_only=True, min_length=8)
    email      = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name  = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Creates a new Django User account.  No event code or selfie needed.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response(
            {
                'id':         user.id,
                'username':   user.username,
                'email':      user.email,
                'first_name': user.first_name,
                'last_name':  user.last_name,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Current-user view (returns minimal info; attendee may not exist yet)
# ---------------------------------------------------------------------------
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        base = {
            'id':         user.id,
            'username':   user.username,
            'email':      user.email,
            'first_name': user.first_name,
            'last_name':  user.last_name,
        }

        # Attendee record is optional — user may not have joined an event yet
        try:
            attendee = Attendee.objects.select_related('user', 'event').get(user=user)
            base.update({
                'attendee_id': attendee.id,
                'event_id':    attendee.event_id,
                'event_name':  attendee.event.name,
                'selfie':      attendee.selfie.url if attendee.selfie else None,
            })
        except Attendee.DoesNotExist:
            base.update({'attendee_id': None, 'event_id': None, 'event_name': None, 'selfie': None})

        return Response(base)

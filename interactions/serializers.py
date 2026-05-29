from rest_framework import serializers
from interactions.models import Interaction


class InteractionDetailSerializer(serializers.ModelSerializer):
    connected_attendee = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()

    class Meta:
        model = Interaction
        fields = [
            'id',
            'event',
            'event_name',
            'interaction_score',
            'connected_attendee',
        ]

    def get_event_name(self, obj):
        if obj.event:
            return obj.event.name
        return None

    def get_connected_attendee(self, obj):
        request = self.context.get('request')

        current_attendee = getattr(request, 'current_attendee', None)

        if not current_attendee:
            return None

        other = (
            obj.attendee2
            if obj.attendee1_id == current_attendee.id
            else obj.attendee1
        )

        return {
            "id": other.id,
            "username": other.user.username if other.user else None,
            "email": other.user.email if other.user else None,
            "role": getattr(other, 'role', 'Attendee'),
            "selfie": other.selfie.url if getattr(other, 'selfie', None) else None,
        }


class InteractionListSerializer(serializers.ModelSerializer):
    attendee1_username = serializers.CharField(
        source='attendee1.user.username',
        read_only=True
    )

    attendee2_username = serializers.CharField(
        source='attendee2.user.username',
        read_only=True
    )

    event_name = serializers.SerializerMethodField()

    class Meta:
        model = Interaction
        fields = [
            'id',
            'event',
            'event_name',
            'interaction_score',
            'attendee1',
            'attendee2',
            'attendee1_username',
            'attendee2_username',
        ]

    def get_event_name(self, obj):
        if obj.event:
            return obj.event.name
        return None
from rest_framework import serializers
from .models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_id', 'ticket_title', 'ticket_description',
            'customer', 'engineer', 'school', 'status',
            'created_on', 'is_resolved', 'is_assigned_to_engineer',
            'resolution_steps', 'phone_number', 'image', 'up_video',
        ]
        read_only_fields = ['id', 'ticket_id', 'created_on']

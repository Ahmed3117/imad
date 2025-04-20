from rest_framework import serializers
from .models import Room, Message

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'code', 'status', 'created_at', 'agent']
        read_only_fields = ['code', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    room_code = serializers.CharField(source='room.code', read_only=True)  # Add room_code
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['text', 'sender', 'is_agent', 'timestamp', 'room_code']  # Include room_code

    def get_sender(self, obj):
        return obj.sender.username if obj.sender else 'Anonymous'
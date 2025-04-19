from rest_framework import serializers
from notification.models import Notification

class StudentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['text','is_read','created_at']
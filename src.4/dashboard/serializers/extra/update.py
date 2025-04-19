from rest_framework import serializers
from extra.models import Update

class UpdateSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Update
        fields = ['id', 'text', 'status', 'status_display', 'updated', 'created']
        read_only_fields = ['id', 'updated', 'created']

    def get_status_display(self, obj):
        return obj.get_status_display()
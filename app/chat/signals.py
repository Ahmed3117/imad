from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChatRoom
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import ChatRoomSerializer

@receiver(post_save, sender=ChatRoom)
def announce_new_room(sender, instance, created, **kwargs):
    if created:
        # Broadcast new room to all dashboard clients
        channel_layer = get_channel_layer()
        serializer = ChatRoomSerializer(instance)
        async_to_sync(channel_layer.group_send)(
            "chat_rooms",
            {
                "type": "new_room",
                "room": serializer.data
            }
        )
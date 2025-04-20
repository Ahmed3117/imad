from rest_framework import generics, permissions
from .models import Room, Message, generate_unique_code
from .serializers import RoomSerializer, MessageSerializer
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

class RoomListCreate(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        code = generate_unique_code()
        room = serializer.save(code=code)

        # Broadcast the new room to all clients
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "rooms",
            {
                'type': 'room_created',
                'room': {
                    'code': room.code,
                    'status': room.status,
                    'created_at': room.created_at.isoformat(),
                    'agent': room.agent.username if room.agent else None
                }
            }
        )

class MessageListCreate(generics.ListCreateAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_code = self.kwargs['room_code']  # Get room_code from URL
        room = Room.objects.get(code=room_code)  # Get the room by code
        return Message.objects.filter(room=room).order_by('timestamp')  # Filter by room

@api_view(['POST'])
def end_chat(request, room_code):
    try:
        room = Room.objects.get(code=room_code)
        # room.status = 'finished'
        # room.save()
        room.delete()  
        return Response({'status': 'success', 'message': 'Chat room marked as finished and deleted.'})
    except Room.DoesNotExist:
        return Response({'status': 'error', 'message': 'Room not found.'}, status=404)

def room_status(request, room_code):
    """Return the status of a room"""
    try:
        room = Room.objects.get(code=room_code)
        return JsonResponse({'status': room.status})
    except Room.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)


def contact_page(request):
    """Render the contact page where clients can start a chat."""
    return render(request, 'chat/contact.html')

@login_required
def dashboard_page(request):
    """Render the customer service dashboard."""
    is_agent = request.user.is_authenticated and request.user.is_superuser
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Access denied.'}, status=403)
    return render(request, 'chat/dashboard.html', {"is_agent": is_agent})

def chat_room(request, room_code):
    is_agent = request.user.is_authenticated and request.user.is_superuser
    return render(request, 'chat/chat_room.html', {"room_code": room_code, "is_agent": is_agent})


 

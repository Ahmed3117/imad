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
from django.utils import timezone

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
    
    def perform_create(self, serializer):
        room_code = self.kwargs['room_code']
        room = Room.objects.get(code=room_code)
        user = self.request.user
        
        # Create the message
        message = serializer.save(room=room, sender=user)
        
        # Update unread counts based on sender type
        if user.is_superuser or user.role == 'cs':
            # Message from CS/superuser, increment user_unread_count
            room.user_unread_count += 1
        else:
            # Message from regular user, increment admin_unread_count
            room.admin_unread_count += 1
            
        room.save()
        
        # Broadcast unread count update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "rooms",
            {
                'type': 'unread_count_update',
                'room_code': room.code,
                'admin_unread': room.admin_unread_count,
                'user_unread': room.user_unread_count
            }
        )

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

@api_view(['POST'])
def open_room(request, room_code):
    try:
        room = Room.objects.get(code=room_code)
        user = request.user
        
        # Update room status and set agent
        room.status = 'opened'
        room.agent = user
        
        # If this is a CS user or superuser and no first_opener is set, set it
        if (user.is_superuser or user.role == 'cs') and not room.first_opener:
            room.first_opener = user
        
        # Update last join time based on user type
        if user.is_superuser or user.role == 'cs':
            room.last_cs_join_time = timezone.now()
            # Reset admin unread count when a CS/superuser joins
            room.admin_unread_count = 0
        else:
            room.last_user_join_time = timezone.now()
            # Reset user unread count when a regular user joins
            room.user_unread_count = 0
            
        room.save()
        
        # Broadcast room status update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "rooms",
            {
                'type': 'room_status',
                'room_code': room.code,
                'status': room.status,
                'agent': room.agent.username if room.agent else None,
                'first_opener': room.first_opener.username if room.first_opener else None
            }
        )
        
        return Response({'status': 'success', 'message': 'Room opened successfully.'})
    except Room.DoesNotExist:
        return Response({'status': 'error', 'message': 'Room not found.'}, status=404)

@api_view(['POST'])
def join_room(request, room_code):
    try:
        room = Room.objects.get(code=room_code)
        user = request.user
        
        # Update last join time based on user type
        if user.is_superuser or user.role == 'cs':
            room.last_cs_join_time = timezone.now()
            # Reset admin unread count when a CS/superuser joins
            room.admin_unread_count = 0
        else:
            room.last_user_join_time = timezone.now()
            # Reset user unread count when a regular user joins
            room.user_unread_count = 0
            
        room.save()
        
        # Broadcast unread count update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "rooms",
            {
                'type': 'unread_count_update',
                'room_code': room.code,
                'admin_unread': room.admin_unread_count,
                'user_unread': room.user_unread_count
            }
        )
        
        return Response({'status': 'success', 'message': 'Joined room successfully.'})
    except Room.DoesNotExist:
        return Response({'status': 'error', 'message': 'Room not found.'}, status=404)

@login_required
def room_list(request):
    """
    Return a list of all rooms with proper agent username serialization.
    """
    if request.method == 'GET':
        rooms = Room.objects.all().order_by('-created_at')
        rooms_data = []
        
        for room in rooms:
            # Properly serialize the agent with username
            agent_data = None
            if room.agent:
                agent_data = {
                    'id': room.agent.id,
                    'username': room.agent.username,
                    'role': room.agent.role
                }
            
            # Properly serialize the first opener with username
            first_opener_data = None
            if room.first_opener:
                first_opener_data = {
                    'id': room.first_opener.id,
                    'username': room.first_opener.username,
                    'role': room.first_opener.role
                }
            
            # Include unread counts in the response
            rooms_data.append({
                'code': room.code,
                'status': room.status,
                'created_at': room.created_at.isoformat(),
                'agent': agent_data,
                'first_opener': first_opener_data,
                'admin_unread_count': room.admin_unread_count,
                'user_unread_count': room.user_unread_count,
                'last_cs_join_time': room.last_cs_join_time.isoformat() if room.last_cs_join_time else None,
                'last_user_join_time': room.last_user_join_time.isoformat() if room.last_user_join_time else None
            })
        
        return JsonResponse(rooms_data, safe=False)
    
    # Handle POST for room creation...

@login_required
def room_status(request, room_code):
    """
    Return the status of a specific room with unread counts and agent username.
    """
    try:
        room = Room.objects.get(code=room_code)
        
        # Properly serialize the agent with username
        agent_data = None
        if room.agent:
            agent_data = {
                'id': room.agent.id,
                'username': room.agent.username,
                'role': room.agent.role
            }
        
        # Properly serialize the first opener with username
        first_opener_data = None
        if room.first_opener:
            first_opener_data = {
                'id': room.first_opener.id,
                'username': room.first_opener.username,
                'role': room.first_opener.role
            }
        
        data = {
            'status': room.status,
            'agent': agent_data,
            'first_opener': first_opener_data,
            'admin_unread_count': room.admin_unread_count,
            'user_unread_count': room.user_unread_count,
            'last_cs_join_time': room.last_cs_join_time.isoformat() if room.last_cs_join_time else None,
            'last_user_join_time': room.last_user_join_time.isoformat() if room.last_user_join_time else None
        }
        
        return JsonResponse(data)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Room not found'}, status=404)


def contact_page(request):
    """Render the contact page where clients can start a chat."""
    return render(request, 'chat/contact.html')

@login_required
def dashboard_page(request):
    """Render the customer service dashboard."""
    is_agent = request.user.is_authenticated and (request.user.is_superuser or request.user.role == 'cs')
    if not is_agent:
        return JsonResponse({'status': 'error', 'message': 'Access denied.'}, status=403)
    return render(request, 'chat/dashboard.html', {"is_agent": is_agent})

def chat_room(request, room_code):
    """Render the chat room page and update join times."""
    is_agent = request.user.is_authenticated and (request.user.is_superuser or request.user.role == 'cs')
    
    # Update join times when entering the chat room
    try:
        room = Room.objects.get(code=room_code)
        user = request.user
        
        # Update last join time based on user type
        if user.is_authenticated:
            if user.is_superuser or user.role == 'cs':
                room.last_cs_join_time = timezone.now()
                # Reset admin unread count when a CS/superuser joins
                room.admin_unread_count = 0
            else:
                room.last_user_join_time = timezone.now()
                # Reset user unread count when a regular user joins
                room.user_unread_count = 0
                
            room.save()
            
            # Broadcast unread count update
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "rooms",
                {
                    'type': 'unread_count_update',
                    'room_code': room.code,
                    'admin_unread': room.admin_unread_count,
                    'user_unread': room.user_unread_count
                }
            )
    except Room.DoesNotExist:
        pass
    
    return render(request, 'chat/chat_room.html', {"room_code": room_code, "is_agent": is_agent})
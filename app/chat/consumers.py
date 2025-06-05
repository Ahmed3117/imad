import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from .models import Room, Message
from asgiref.sync import sync_to_async

from channels.exceptions import StopConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'chat_{self.room_code}'

        # Check if room exists and is active before accepting connection
        try:
            room = await sync_to_async(Room.objects.get)(code=self.room_code)
            if room.status == 'finished':
                # Room is finished, reject connection with message
                await self.accept()
                await self.send(text_data=json.dumps({
                    'type': 'chat_ended',
                    'room_code': self.room_code,
                    'message': 'This chat has been ended.'
                }))
                await self.close(code=1000)
                return
        except Room.DoesNotExist:
            # Room doesn't exist, reject connection with message
            await self.accept()
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'This chat room no longer exists.'
            }))
            await self.close(code=1000)
            return
        
        # Room exists and is active, proceed with connection
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Reset unread count based on user type
        user = self.scope['user']
        is_agent = user.is_staff if user.is_authenticated else False
        
        if is_agent:
            # Reset admin unread count when an admin connects to the room
            await sync_to_async(room.reset_admin_unread)()
            
            # Broadcast the updated unread count to all dashboard clients
            await self.channel_layer.group_send(
                "rooms",
                {
                    'type': 'unread_count_update',
                    'room_code': room.code,
                    'admin_unread': 0,  # Reset to 0
                    'user_unread': room.user_unread_count  # Keep user unread count
                }
            )
        else:
            # Reset user unread count when a user connects to the room
            await sync_to_async(room.reset_user_unread)()
            
            # Broadcast the updated unread count to all dashboard clients
            await self.channel_layer.group_send(
                "rooms",
                {
                    'type': 'unread_count_update',
                    'room_code': room.code,
                    'admin_unread': room.admin_unread_count,  # Keep admin unread count
                    'user_unread': 0  # Reset to 0
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']
        is_agent = user.is_staff if user.is_authenticated else False

        try:
            if 'type' in data and data['type'] == 'end_chat':  # Handle end chat action
                room = await sync_to_async(Room.objects.get)(code=self.room_code)
                room.status = 'finished'
                await sync_to_async(room.save)()
                
                # Broadcast the "end chat" event to all participants BEFORE deleting the room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_ended',
                        'room_code': self.room_code,
                        'ended_by': user.username if user.is_authenticated else 'Anonymous',
                        'is_agent': is_agent
                    }
                )
                
                # Add a small delay to ensure message is delivered before room deletion
                await asyncio.sleep(3)
                
                # Delete the room after notifying everyone
                await sync_to_async(room.delete)()
                
            else:  # Handle regular chat messages
                room = await sync_to_async(Room.objects.get)(code=self.room_code)
                # Check if room is still active
                if room.status == 'finished':
                    await self.send(text_data=json.dumps({
                        'type': 'chat_ended',
                        'room_code': self.room_code,
                        'message': 'This chat has been ended.'
                    }))
                    await self.close(code=1000)
                    return
                    
                message = data['message']
                # Create the message
                await sync_to_async(Message.objects.create)(
                    room=room,
                    text=message,
                    sender=user if user.is_authenticated else None,
                    is_agent=is_agent
                )
                
                # Fetch updated unread counts after message creation
                room = await sync_to_async(Room.objects.get)(code=self.room_code)
                
                # Broadcast the message to the chat room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': user.username if user.is_authenticated else 'Anonymous',
                        'is_agent': is_agent
                    }
                )
                
                # Broadcast the updated unread counts to all dashboard clients
                await self.channel_layer.group_send(
                    "rooms",
                    {
                        'type': 'unread_count_update',
                        'room_code': room.code,
                        'admin_unread': room.admin_unread_count,
                        'user_unread': room.user_unread_count
                    }
                )
        except Room.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'This chat room no longer exists.'
            }))
            await self.close(code=1000)  # Close the WebSocket connection

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'is_agent': event['is_agent']
        }))

    async def chat_ended(self, event):
        # Send the chat_ended event to the client
        await self.send(text_data=json.dumps({
            'type': 'chat_ended',
            'room_code': event['room_code'],
            'ended_by': event.get('ended_by', 'Unknown user'),
            'is_agent': event.get('is_agent', False)
        }))
        
        # Explicitly close the WebSocket connection after sending the message
        await self.close(code=1000)  # Normal closure
        
    async def unread_count_update(self, event):
        # Send unread count update to the client
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'room_code': event['room_code'],
            'admin_unread': event['admin_unread'],
            'user_unread': event['user_unread']
        }))


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("rooms", self.channel_name)  # Add to "rooms" group

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("rooms", self.channel_name)  # Remove from "rooms" group

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'open_room':
            room_code = data['room_code']
            user = self.scope['user']
            if user.is_authenticated:
                room = await sync_to_async(Room.objects.get)(code=room_code)
                if room.status == 'active':
                    room.status = 'opened'
                    room.agent = user
                    await sync_to_async(room.save)()
                    
                    # Reset admin unread count when an admin opens the room
                    await sync_to_async(room.reset_admin_unread)()
                    
                    await self.channel_layer.group_send(
                        "rooms",
                        {
                            'type': 'room_update',
                            'room_code': room.code,
                            'status': 'opened',
                            'agent': user.username,
                            'admin_unread': 0,  # Reset to 0
                            'user_unread': room.user_unread_count  # Keep user unread count
                        }
                    )
        elif data['type'] == 'end_chat':  # Handle end chat action
            room_code = data['room_code']
            room = await sync_to_async(Room.objects.get)(code=room_code)
            room.status = 'finished'
            await sync_to_async(room.save)()
            await sync_to_async(room.delete)()  # Delete the room
            await self.channel_layer.group_send(
                "rooms",
                {
                    'type': 'room_deleted',
                    'room_code': room.code,
                }
            )

    async def room_update(self, event):
        # Include unread counts in the room update if available
        response = {
            'type': 'room_status',
            'room_code': event['room_code'],
            'status': event['status'],
            'agent': event['agent']
        }
        
        # Add unread counts if they exist in the event
        if 'admin_unread' in event:
            response['admin_unread'] = event['admin_unread']
        if 'user_unread' in event:
            response['user_unread'] = event['user_unread']
            
        await self.send(text_data=json.dumps(response))

    async def room_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'room_deleted',
            'room_code': event['room_code'],
        }))

    async def room_created(self, event):
        # Send new room data to the client
        await self.send(text_data=json.dumps({
            'type': 'room_created',
            'room': event['room']
        }))
        
    async def unread_count_update(self, event):
        # Send unread count update to all dashboard clients
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'room_code': event['room_code'],
            'admin_unread': event['admin_unread'],
            'user_unread': event['user_unread']
        }))
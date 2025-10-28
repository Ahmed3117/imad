from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/rooms/$', consumers.RoomConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_code>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
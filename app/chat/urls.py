from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('contact/', views.contact_page, name='contact'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    path('rooms/<str:room_code>/', views.chat_room, name='chat-room'),
    path('rooms/', views.RoomListCreate.as_view(), name='room-list-create'),
    path('rooms/<str:room_code>/messages/', views.MessageListCreate.as_view(), name='message-list-create'),
    path('rooms/<str:room_code>/end/', views.end_chat, name='end-chat'),
    path('rooms/<str:room_code>/status/', views.room_status, name='room_status'),

]
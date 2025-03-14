from django.urls import path

from subscriptions.zoom import create_zoom_meeting


app_name='subscriptions'


urlpatterns = [
    path('create-meeting/', create_zoom_meeting, name='create-meeting'),
]





from django.urls import path

from freemeet.views import request_free_meet, send_meeting_email, send_whatsapp

app_name='freemeet'
urlpatterns = [
    path('request_free_meet/', request_free_meet, name='request_free_meet'),
    path('send_whatsapp/<int:freemeet_id>/', send_whatsapp, name='send_whatsapp'),
    path('send_meeting_email/<int:freemeet_id>/', send_meeting_email, name='send_meeting_email'),
]





from django.urls import path
from .views import levels, send_join_request

app_name='courses'

urlpatterns = [
    path('levels/',levels,name='levels'),
    path('send-join-request/<int:course_id>/', send_join_request, name='send_join_request'),
]
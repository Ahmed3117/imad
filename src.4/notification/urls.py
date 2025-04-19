from django.urls import path
from . import views
urlpatterns = [
    path("notification-read-update", views.NotificationReadUpdate.as_view(), name="NotificationReadUpdate")
]

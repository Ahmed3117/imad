from django.urls import path
from . import views
urlpatterns = [
    path("convert-video", views.convert_video, name="convert-video"),
]
from django.urls import path
from . import views
urlpatterns = [
    path("news-list", views.NewsListAPIView.as_view(), name="NewsListAPIView")
]

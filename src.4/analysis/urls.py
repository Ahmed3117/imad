from django.urls import path
from . import views
urlpatterns = [
    path("profile-analysis", views.ProfileAnalysis.as_view(), name="ProfileAnalysis"),
    path("user-activity-analysis", views.UserActivityAnalysis.as_view(), name="UserActivityAnalysis"),
]

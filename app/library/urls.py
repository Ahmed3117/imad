from django.urls import path
from . import views
app_name='library'

urlpatterns = [
    path('course-library/', views.course_library_view, name='course_library'),
    path('get-study-groups/', views.get_study_groups, name='get_study_groups'),
    path('share-resources/', views.share_resources, name='share_resources'),
]
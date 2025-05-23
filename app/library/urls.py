from django.urls import path
from . import views
app_name='library'

urlpatterns = [
    path('', views.course_library_view, name='course_library'),
    path('add/', views.add_course_library, name='add_course_library'),
    path('edit/<int:library_id>/', views.edit_course_library, name='edit_course_library'),
    path('delete/<int:library_id>/', views.delete_course_library, name='delete_course_library'),
    path('create_category/', views.create_library_category, name='create_library_category'),
    path('get_study_groups/', views.get_study_groups, name='get_study_groups'),
    path('share_resources/', views.share_resources, name='share_resources'),
]
from django.urls import path
from . import views
urlpatterns = [
    path('unit-content-subscription/<int:unit_id>', views.UnitContentSubscription.as_view(), name='unit-content-subscription'),
    path('access-content/<int:course_id>/<str:content_type>/<int:content_id>', views.AccessContent.as_view(), name='access-content'),
    path('access-lesson-by-code/<int:lesson_id>', views.AccessLessonByCode.as_view(), name='AccessLessonByCode'),
]
from django.urls import path

from subscriptions.zoom import create_zoom_meeting, get_meeting_status
from subscriptions.views import (
    StudyGroupReportView,
    teacher_timetable,
    student_timetable,
    admin_timetable,
)


app_name='subscriptions'


urlpatterns = [
    path('create-meeting/', create_zoom_meeting, name='create-meeting'),
    path('meeting-status/<str:meeting_id>/', get_meeting_status, name='meeting_status'),

    path('studygroup/<int:pk>/report/', StudyGroupReportView.as_view(), name='studygroup_report'),
    
    # Timetable URLs
    path('timetable/teacher/', teacher_timetable, name='teacher_timetable'),
    path('timetable/student/', student_timetable, name='student_timetable'),
    path('timetable/admin/', admin_timetable, name='admin_timetable'),
]






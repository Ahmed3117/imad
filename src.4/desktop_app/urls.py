from django.urls import path
from . import views

urlpatterns = [
    path('student-list/', views.StudentList.as_view(), name='student-list'),
    path('course-list/', views.CourseList.as_view(), name='course-list'),
    path('lesson-list/', views.LessonList.as_view(), name='lesson-list'),
    path('lesson-views/<int:lesson_id>/', views.LessonViewsList.as_view(), name='video-views-list'),
    path('exam-list/', views.ExamList.as_view(), name='exam-list'),
    path('exam-results/<int:exam_id>/', views.ExamResultList.as_view(), name='exam-results-list'),
    path('subscribe-many-users/', views.SubscribeManyUsers.as_view(), name='subscribe-many-users'),
    path('unsubscribe-many-users/', views.UnSubscribeManyUsers.as_view(), name='unsubscribe-many-users'),
    path('submit-result-exam/', views.SubmitResultExam.as_view(), name='unsubscribe-many-users'),
    path('center-list/', views.CenterList.as_view(), name='center-list'),
    path('center-create/',views.CenterCreate.as_view(), name='center-create'),
    path('lecture-list/', views.LectureList.as_view(), name='lecture-list'),
    path('lecture-create/',views.LectureCreate.as_view(), name='lecture-create'),
    path('attendance-list/', views.AttendanceList.as_view(), name='attendance-list'),
    path('attendance-create/',views.AttendanceCreate.as_view(), name='attendance-create'),
]



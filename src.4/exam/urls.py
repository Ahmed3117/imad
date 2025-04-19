from django.urls import path
from . import views

urlpatterns = [
    path('<int:exam_id>/start/', views.StartExam.as_view(), name='start-exam'),
    path('<int:exam_id>/submit/', views.SubmitExam.as_view(), name='submit-exam'),
    path('exam-results/', views.StudentExamResultsView.as_view(), name='student-exam-results'),
    path('<int:exam_id>/result', views.GetMyExamResult.as_view(), name='get-my-exam-result'),
]



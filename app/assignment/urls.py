from django.urls import path
app_name='assignment'
from . import views

urlpatterns = [
    # Teacher URLs
    path('lecture/<int:lecture_pk>/assignment/create/', 
         views.assignment_create, 
         name='assignment_create'),
    path('assignment/<int:pk>/edit/', 
         views.assignment_edit, 
         name='assignment_edit'),
    path('assignment/<int:pk>/delete/', 
         views.assignment_delete, 
         name='assignment_delete'),
    path('assignment/<int:pk>/', 
         views.assignment_detail, 
         name='assignment_detail'),
    path('answer/<int:pk>/grade/', 
         views.grade_answer, 
         name='grade_answer'),
    
    # Student URLs
    path('group/<int:group_pk>/assignments/', 
         views.student_assignment_list, 
         name='student_assignment_list'),
    path('assignment/<int:assignment_pk>/submit/', 
         views.submit_answer, 
         name='submit_answer'),
    path('answer/<int:pk>/edit/', 
         views.edit_answer, 
         name='edit_answer'),
    path('answer/<int:pk>/delete/', 
         views.delete_answer, 
         name='delete_answer'),
    
    # Report URLs
    path('group/<int:pk>/grades/', 
         views.studygroup_grades, 
         name='studygroup_grades'),
    path('group/<int:pk>/student/<int:student_pk>/grades/', 
         views.student_grades, 
         name='student_grades'),
]






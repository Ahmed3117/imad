from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('register_user/', views.register_user, name='register_user'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
        
    path('login/', views.user_login, name='login'),
    path('login_student/', views.login_student, name='login_student'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('parent_dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('add_student/', views.add_student, name='add_student'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('course/<int:course_id>/sessions/<str:student_username>/', views.session_details, name='session_details'),
    path('session/<int:session_id>/complete/', views.mark_session_completed, name='mark_session_completed'),
    path('exam/<int:exam_id>/start/', views.start_exam, name='start_exam'),
    path('exam/submit/<int:exam_id>/', views.submit_exam, name='submit_exam'),
    
    
    path('get-available-slots/', views.get_available_slots, name='get_available_slots'),
    path('create-appointment/', views.create_appointment, name='create_appointment'),

]





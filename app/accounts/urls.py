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
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('profile/<int:study_group_id>/lectures/', views.study_group_lectures, name='lectures'),
    path('study-group/<int:study_group_id>/add-lecture/', views.add_lecture, name='add_lecture'),
    path('lecture/<int:lecture_id>/update/', views.update_lecture, name='update_lecture'),
    path('lecture/<int:lecture_id>/delete/', views.delete_lecture, name='delete_lecture'),
    path('lecture/<int:lecture_id>/reschedule/', views.reschedule_lecture, name='reschedule_lecture'),
    path('lecture/<int:lecture_id>/add-files/', views.add_lecture_files, name='add_lecture_files'),
    path('lecture-file/<int:file_id>/delete/', views.delete_lecture_file, name='delete_lecture_file'),



]





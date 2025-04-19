from django.urls import path
from . import views
urlpatterns = [
    #* < ==============================[ <- Auth  -> ]============================== > ^#
    path("student-sign-in", views.StudentSignInView.as_view(), name="student_sign_in"),
    path("student-sign-up", views.StudentSignUpView.as_view(), name="student_sign_up"),
    path("student-sign-code", views.StudentSignCodeView.as_view(), name="student_sign_code"),
    #* < ==============================[ <- Reset Password  -> ]============================== > ^#
    path("request-reset-password", views.RequestResetPasswordView.as_view(), name="request_password_reset"),
    path("verify-pin-code", views.VerifyPinCodeView.as_view(), name="verify_pin_code"),
    path("reset-password", views.ResetPasswordView.as_view(), name="reset_password"),
    #* < ==============================[ <- Profile  -> ]============================== > ^#
    path("student-profile", views.StudentProfileView.as_view(), name="student_profile"),
    #* < ==============================[ <- Invoice  -> ]============================== > ^#
    path("student-invoice-list", views.StudentInvoiceList.as_view(), name="student_invoice"),
    #* < ==============================[ <- Subscription  -> ]============================== > ^#
    path("course-subscription-list", views.CourseSubscriptionList.as_view(), name="student_course_subscription"),
    path("lesson-subscription-list", views.LessonSubscriptionList.as_view(), name="LessonSubscriptionList"),
    path("course-subscription-details/<int:subscription_id>", views.CourseSubscriptionDetails.as_view(), name="student_course_subscription_Details"),
    #* < ==============================[ <- View  -> ]============================== > ^#
    path("lesson-views-list", views.ViewsLessonList.as_view(), name="lesson-views-list"),
    #* < ==============================[ <- Notification  -> ]============================== > ^#
    path("notification-list", views.NotificationList.as_view(), name="notification-list"),
    #* < ==============================[ <- CENTER -> ]============================== > ^#
    path("center-result-exam-list", views.CenterResultExamList.as_view(), name="CenterResultExamList"),
    path("center-attendance-list", views.CenterAttendanceList.as_view(), name="CenterAttendanceList"),
    
]


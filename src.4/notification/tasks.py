from celery import shared_task
from course.models import *
from subscription.models import CourseSubscription
from .models import Notification


@shared_task
def notifications_new_lesson(course_id, lesson_name):
    course = Course.objects.get(id=course_id)
    subscriptions = CourseSubscription.objects.filter(course=course, active=True)

    notifications = [
        Notification(
            student=subscription.student,
            text=f"تمت إضافة درس جديد '{lesson_name}' إلى الكورس '{course.name}'."
        )
        for subscription in subscriptions
    ]
    Notification.objects.bulk_create(notifications)
    
    # send whatsapp massage
    # for subscription in subscriptions:
    #     student = subscription.student
    #     if student.user.username:  
    #         message = f"Hello {student.name}, a new lesson '{lesson_name}' has been added to your course '{course.name}'."
    #         response = send_whatsapp_massage(student.user.username, message)
from django.db.models. signals import post_save,pre_save,pre_delete
from django.template.loader import render_to_string
from django.dispatch import receiver
from rest_framework import status
from django.conf import settings
from course.models import *
from student.models import *
from subscription.models import CourseSubscription,LessonSubscription
from .models import *
from view.models import LessonView
from student.utils import send_whatsapp_massage
import time
import requests


@receiver(post_save, sender=Invoice)
def pay_course(sender, instance, created, **kwargs):


    # Pay Course
    if instance.pay_status == "C" and instance.course:
        student_use_has_course = CourseSubscription.objects.filter(student=instance.student,course=instance.course,active=True).exists()
        if not student_use_has_course:
        # Create or get CourseSubscription
            create_course = CourseSubscription.objects.create(
                student=instance.student,
                course=instance.course,
                invoice = instance,
                active=True
            )


            # Send WhatsApp message
            if settings.USE_WHATSAPP:
                
                admin_phone = settings.ADMIN_PHONE 
                massage = f'{instance.sequence}تم دفع فتورة برقم {instance.student.name} من قبل الطالب {instance.student.user.username} رقم الهاتف'
                send_whatsapp_massage(
                    phone_number=admin_phone,
                    massage=massage
                )



                message = (
                    f"مرحباً {instance.student.name}،\n\n"
                    f"تم الاشتراك في كورس '{instance.course.name}' بنجاح.\n"
                    f"رقم الفاتورة: {instance.sequence}\n\n"
                    "شكراً لك!"
                )

                send_whatsapp_massage(
                    phone_number=instance.student.username,
                    massage=message
                )
    
    # Pay Course Collection
    elif instance.pay_status == "C" and instance.course_collection :

        for i in instance.course_collection.courses.all():
            student_use_has_course = CourseSubscription.objects.filter(student=instance.student,course=i,active=True).exists()
            if not student_use_has_course:
                create = CourseSubscription.objects.create(
                    student=instance.student,
                    invoice= instance,
                    course=i,
                    active=True,
                )


        #Send WhatsApp message
        if settings.USE_WHATSAPP:
            
            admin_phone = settings.ADMIN_PHONE 
            massage = f'{instance.sequence}تم دفع فتورة برقم {instance.student.name} من قبل الطالب {instance.student.user.username} رقم الهاتف'
            send_whatsapp_massage(
                phone_number=admin_phone,
                massage=massage
            )
            
            
            message = (
                f"مرحباً {instance.student.name}،\n\n"
                f"تم الاشتراك في عرض '{instance.course_collection.name}' بنجاح.\n"
                f"رقم الفاتورة: {instance.sequence}\n\n"
                "شكراً لك!"
            )
            send_whatsapp_massage(
                phone_number=instance.student.user.username,
                massage=message
            )

    # Pay Course Lesson
    elif instance.pay_status == "C" and instance.lesson :
        student_use_has_lesson = LessonSubscription.objects.filter(student=instance.student,active=True,lesson=instance.lesson).exists()

        if not student_use_has_lesson:

            LessonSubscription.objects.create(
                student=instance.student,
                lesson=instance.lesson,
                invoice=instance,
                active=True,
            )


            # Send WhatsApp message
            if settings.USE_WHATSAPP:
                admin_phone = settings.ADMIN_PHONE 
                massage = f'{instance.sequence}تم دفع فتورة برقم {instance.student.name} من قبل الطالب {instance.student.user.username} رقم الهاتف'
                send_whatsapp_massage(
                    phone_number=admin_phone,
                    massage=massage
                )
                
                
                
                message = (
                    f"مرحباً {instance.student.name}،\n\n"
                    f"تم الاشتراك في درس '{instance.lesson.name}' بنجاح.\n"
                    f"رقم الفاتورة: {instance.sequence}\n\n"
                    "شكراً لك!"
                )

                send_whatsapp_massage(
                    phone_number=instance.student.user.username,
                    massage=message
                )


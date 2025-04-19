from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from student.utils import  send_whatsapp_massage
from student.models import *
from course.models import *
from invoice.models import *
from .models import Notification
from .tasks import notifications_new_lesson

@receiver(post_save, sender=Lesson)
def new_lesson(sender, instance, created, *args, **kwargs):
    if created:
        notifications_new_lesson.delay(instance.unit.course.id, instance.name)


@receiver(pre_save, sender=Invoice)
def pay_invoice(sender, instance, *args, **kwargs):
    text = None
    
    if instance.pay_status == "P":
        text = f"تم انشاء فتورة برقم {instance.sequence} من فضلك تأكد من دفع الفتورة قبل معاد {instance.expires_at}"
    elif instance.pay_status == "C":
        course_or_collection_or_lesson = instance.course or instance.course_collection or instance.lesson
        if course_or_collection_or_lesson:
            text = f"تم الاشتراك في {course_or_collection_or_lesson.name} بنجاح 🎉"
    
    if text:
        Notification.objects.create(student=instance.student, text=text)
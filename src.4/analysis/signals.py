from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from student.models import *
from invoice.models import *
from view.models import LessonView
from .models import *
"""
watching_videos
submitting_answers
course_subscribe

"""

@receiver(post_save, sender=Invoice)
def pay_course_point(sender, instance, created, **kwargs):
    if created and instance.pay_status == "C":
        course_or_collection = instance.course or instance.course_collection
        if course_or_collection:
            StudentPoint.objects.create(
                student=instance.student,
                point_type="course_subscribe",
                points=course_or_collection.points,
                points_note=f"Pay for {course_or_collection.name}"
            )
            instance.student.points += course_or_collection.points
            instance.student.save()




@receiver(post_save, sender=LessonView)
def lesson_view_point(sender, instance, created, **kwargs):
    if created and instance.counter >= 1:
        StudentPoint.objects.create(
            student=instance.student,
            point_type="watching_videos",
            points=instance.lesson.points,
            points_note=f"Watch {instance.lesson.name}"
        )
        student = instance.student
        student.points += instance.lesson.points
        student.save()

from django.db import models
from django.core.exceptions import ValidationError
# Create your models here.
from accounts.models import TeacherInfo, User
from courses.models import Course
from subscriptions.models import Subscription


class TeacherAvailability(models.Model):
    DAYS_OF_WEEK = [
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['teacher', 'day', 'start_time', 'end_time']
        
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
    
    def teacher_courses(self):
        """
        Fetch the courses associated with the teacher from the TeacherInfo model.
        """
        try:
            teacher_info = self.teacher.teacher_info
            return ", ".join([course.name for course in teacher_info.courses.all()])
        except TeacherInfo.DoesNotExist:
            return "No courses assigned"

    teacher_courses.short_description = "Teacher Courses"
    
    def __str__(self):
        return f"{self.teacher.name} - {self.day} ({self.start_time}-{self.end_time} --- {str(self.is_available)})"

class Appointment(models.Model):
    subscription = models.OneToOneField(Subscription, on_delete=models.CASCADE)
    avialability = models.ForeignKey(TeacherAvailability, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.subscription.student.name} - {self.avialability.teacher.name} - {self.avialability.day} ({self.avialability.start_time}-{self.avialability.end_time})"


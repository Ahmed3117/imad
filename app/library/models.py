from django.db import models

from accounts.models import User
from courses.models import Course

# Create your models here.
class CourseLibrary(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='libraries')
    file = models.FileField(upload_to='courseslibraries/')
    def __str__(self):
        return f"{self.course.name} | {self.file.name}"
    
class MyLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mylibraries' , limit_choices_to={'role': 'teacher'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mycourselibraries' , null=True , blank=True)
    file = models.FileField(upload_to='courseslibraries/')
    def __str__(self):
        return f"{self.user.username} | {self.course.name} | {self.file.name}"
    





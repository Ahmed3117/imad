from django.db import models
from student.models import Student
# Create your models here.

class ResultExamCenter(models.Model):
    student = models.ForeignKey(Student,blank=True, null=True ,on_delete=models.CASCADE)
    name = models.CharField(max_length=50,blank=True, null=True)
    lecture = models.CharField(max_length=50,blank=True, null=True)
    date = models.DateField(auto_now=False, auto_now_add=False,blank=True, null=True)
    result_photo = models.CharField(max_length=550,blank=True, null=True)
    result_percentage = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Center(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Lecture(models.Model):
    name = models.CharField(max_length=50,)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    date = models.DateField() # "2024-03-20"
    status = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lecture', 'date')


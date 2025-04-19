from django.db import models
from course.models import Course
from student.models import Student
# Create your models here.

class StudentPoint(models.Model):
    POINT_TYPE_CHOICES = [
        ('watching_videos', 'Watching videos'),
        ('submitting_answers', 'Submitting answers or assignments'),
        ('course_subscribe', 'Course subscribe'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_points")
    points_note = models.CharField(max_length=50,blank=True,null=True)
    point_type = models.CharField(max_length=50,choices=POINT_TYPE_CHOICES)
    points = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.point_type}"
    
class CoursePermission(models.Model):
    COURSE_PERMISSION_CHOICES = [
        ('no_permission', 'No Permission'),
        ('lessonwatch', 'Lesson Watch'),
        ('exam_take', 'Exam Take'),
        ('exam_pass', 'Exam Pass'),
        ('all', 'All'),
    ]

    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='permission')
    open_permission = models.CharField(max_length=20, choices=COURSE_PERMISSION_CHOICES, default='no_permission')

    def __str__(self):
        return f"{self.course.name} - {self.get_open_permission_display()}"



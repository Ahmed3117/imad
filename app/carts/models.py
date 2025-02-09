from django.db import models
from accounts.models import User
# Create your models here.
from courses.models import Course, Level, Track

# CartCourses Model
class CartCourse(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} added {self.course.name} to cart"

class CartTrack(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} added {self.track.name} to cart"

class CartLevel(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} added {self.level.name} to cart"

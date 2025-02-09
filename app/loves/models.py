from django.db import models
from accounts.models import User
# Create your models here.
from courses.models import Course, Track

# LoveCourses Model
class LoveCourse(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='loved_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student.name} loves {self.course.name}"

# LoveTracks Model
class LoveTrack(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='loved_tracks')
    track = models.ForeignKey(Track, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student.name} loves {self.track.name}"

from django.db import models
# Levels Model
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP
from threading import local
from .middleware import get_current_request



class Level(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Track(models.Model):
    name = models.CharField(max_length=200)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='tracks')

    def __str__(self):
        return f"{self.level.name} | {self.name}"


class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='courses/', default='defaults/default.jpg')
    preview_video = models.CharField(max_length=50, blank=True, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='courses')
    track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')

    def __str__(self):
        # Level is required, so it should always be accessible
        level_name = self.level.name if self.level else "No Level"
        
        # Track is optional, so check if it exists
        track_name = self.track.name if self.track else "No Track"
        
        # Return a string with level, track, and name
        return f"{level_name} | {track_name} | {self.name}"


#-----------------------translation models-----------------------------#
class LevelTranslation(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('level', 'language')

    def __str__(self):
        return f"{self.level.name} - {self.language}"


class TrackTranslation(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('track', 'language')

    def __str__(self):
        return f"{self.track.name} - {self.language}"


class CourseTranslation(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('course', 'language')

    def __str__(self):
        return f"{self.course.name} - {self.language}"




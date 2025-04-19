from django.db import models
from accounts.models import User
from courses.models import Course
import requests
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.core.validators import MaxValueValidator,MinValueValidator
from library.models import CourseLibrary


class StudyGroup(models.Model):
    CAPACITY_CHOICES = [
        (1, '1'),
        (3, '3'),
        (5, '5'),
        (10, '10'),
        (20, '20'),
    ]

    name = models.CharField(
        max_length=100,
        blank=True
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='study_groups'
    )
    capacity = models.IntegerField(
        choices=CAPACITY_CHOICES,
        null=True,
        blank=True
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='teaching_groups'
    )
    number_of_expected_lectures = models.PositiveIntegerField()
    join_price = models.DecimalField(max_digits=8, decimal_places=2)
    students = models.ManyToManyField(
        User,
        limit_choices_to={'role': 'student'},
        related_name='study_groups',
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Group-{self.pk}"
            super().save(*args, **kwargs)

    def __str__(self):
        # Safely get level name (should always exist due to CASCADE)
        level_name = self.course.level.name if self.course and self.course.level else ""
        
        # Safely get track name (could be null)
        track_name = self.course.track.name if self.course and self.course.track else ""
        
        # Construct the string with fallbacks 
        return f"{self.name} | {level_name} | {track_name} | {self.course.name} | {self.teacher.name or self.teacher.username }" 
    
class GroupTime(models.Model):
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]

    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='group_times')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    time = models.TimeField()

    def __str__(self):
        return f"{self.get_day_display()} | {self.time}"

class JoinRequest(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='join_requests')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='join_requests')
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='join_requests', blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.group:
            self.group.students.add(self.student)

    def __str__(self):
        return f"Join Request by {self.student.username} for {self.course.name} in {self.group}"

class Lecture(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='lectures')
    live_link = models.URLField(blank=True, null=True)  # created zoom link
    live_link_date = models.DateTimeField(blank=True, null=True)
    duration = models.IntegerField(default=60, validators=[MaxValueValidator(300), MinValueValidator(10)])
    is_finished = models.BooleanField(default=False)
    is_visited = models.BooleanField(default=False)
    finished_date = models.DateTimeField(blank=True, null=True)

    # method to get the meeting id 
    def get_meeting_id(self):
        if not self.live_link:
            return ""
        # Split by '/' and get the last segment
        last_segment = self.live_link.split('/')[-1]
        # Split by '?' to remove query parameters and take the first part
        meeting_id = last_segment.split('?')[0]
        return meeting_id

    def get_status_display(self):
        """Returns a human-readable status with color coding"""
        teacher_note = self.notes.filter(user__userprofile__role='teacher').first()
        if teacher_note:
            return {
                'text': teacher_note.get_lecture_status_display(),
                'class': 'success' if teacher_note.lecture_status == 'completed' 
                        else 'warning' if teacher_note.lecture_status == 'student_delayed' 
                        else 'danger'
            }
        return {'text': 'Pending Review', 'class': 'secondary'}

    def get_average_rating(self):
        """Returns the average rating from student notes"""
        result = self.notes.filter(rating__isnull=False).aggregate(Avg('rating'))
        return result['rating__avg'] or 0

    def get_rating_count(self):
        """Returns the number of ratings submitted"""
        return self.notes.filter(rating__isnull=False).count()

    def __str__(self):
        return f"Lecture: {self.title} for {self.group}"

    class Meta:
        ordering = ['-live_link_date']

class LectureFile(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='lecture_files/')

    def __str__(self):
        return f"File for Lecture: {self.lecture.title}"

class LectureNote(models.Model):
    LECTURE_STATUS_CHOICES = [
        ('completed', 'Completed Successfully'),
        ('student_delayed', 'Delayed or not attendeded by Student'),
        ('teacher_delayed', 'Delayed or not attendeded by Teacher'),
    ]
    
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        null=True, 
        blank=True
    )
    lecture_status = models.CharField(
        max_length=20,
        choices=LECTURE_STATUS_CHOICES,
        default='completed',
        null=True,
        blank=True
    )
    delay_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lecture', 'user')

    def __str__(self):
        return f"Note for {self.lecture.title} by {self.user.username}"

class StudyGroupResource(models.Model):
    studygroup = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    resource = models.ForeignKey(CourseLibrary, on_delete=models.CASCADE)
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('studygroup', 'resource')
    
    def __str__(self):
        return f"{self.studygroup.course.name} | {self.resource.file.name}"











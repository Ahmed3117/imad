
from django.db import models

from accounts.models import User
from subscriptions.models import Lecture
from django.utils import timezone

# Create your models here.
class Assignment(models.Model):
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(
        upload_to='assignments/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_at = models.DateTimeField()
    max_grade = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f"Assignment: {self.title} for {self.lecture.title}"

    def is_past_due(self):
        return timezone.now() > self.due_at

    class Meta:
        ordering = ['-created_at']
        app_label = 'assignment'


class StudentAnswer(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='student_answers'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='assignment_answers'
    )
    answer_text = models.TextField()
    attachment = models.FileField(
        upload_to='student_answers/',
        blank=True,
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    grade = models.PositiveIntegerField(null=True, blank=True)
    teacher_feedback = models.TextField(blank=True)

    def __str__(self):
        return f"Answer by {self.student.username} for {self.assignment.title}"

    def can_edit(self):
        return not self.assignment.is_past_due()

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']
        app_label = 'assignment'
from django.db import models
from accounts.models import User
from courses.models import Course, Session

class Subscription(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="active", choices=[('active', 'Active'), ('waiting', 'Waiting'), ('finished', 'Finished')])
    completed_sessions = models.ManyToManyField(Session, blank=True, related_name='completed_by')

    @property
    def progress(self):
        total_sessions = self.course.coursesessions.count()
        if total_sessions == 0:
            return 0
        completed = self.completed_sessions.count()
        return round((completed / total_sessions) * 100, 2)

    @property
    def is_completed(self):
        return self.status == 'finished'

    def __str__(self):
        return f"{self.student.username} - {self.course} ({self.status})"


class SubscriptionSession(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    session_url = models.CharField(max_length=500, blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.session.title} - {self.subscription.student.username}"






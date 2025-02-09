from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class FreeMeet(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('done', 'Done'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    phone_number = models.CharField(max_length=15)
    student_email = models.EmailField(blank=True, null=True)  # New field for student's email
    respond_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    meet_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FreeMeet Request by {self.student.username} - {self.phone_number}"

    def save(self, *args, **kwargs):
        # Automatically populate student_email from get_user_email method
        if not self.student_email and self.student:
            self.student_email = self.student.get_user_email()
        if not self.phone_number and self.student:
            self.phone_number = self.student.get_user_phone()
        super().save(*args, **kwargs)



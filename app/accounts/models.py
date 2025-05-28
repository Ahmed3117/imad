from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from courses.models import Course


class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
        ('cs', 'Customer Service'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name if self.name else self.username

    def get_first_name(self):
        """Get the first name by splitting the full name."""
        return self.name.split()[0] if self.name else ""

    def get_last_name(self):
        """Get the last name by splitting the full name."""
        return self.name.split()[-1] if self.name else ""

    def get_user_phone(self):
        """Get the user's phone number based on their role."""
        if self.role == "teacher":
            return self.phone or None
        elif self.role == 'student':
            if self.phone:
                return self.phone
            else:
                return None
                
        return None  

    def get_user_email(self):
        """Get the user's email based on their role."""
        if self.role == "teacher":
            return self.email
        elif self.role == 'student':
            if self.email:
                return self.email
            else:
                return None
        return None  # Return None if no email is found

    def get_name(self):
        # get name or username
        if self.name:
            return self.name
        else:
            return self.username

class TeacheroomAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacheroom_account', limit_choices_to={'role': 'teacher'})
    account_id = models.CharField(max_length=100, blank=True, null=True)
    client_id = models.CharField(max_length=100, blank=True, null=True)
    client_secret = models.CharField(max_length=100, blank=True, null=True)
    secret_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    def __str__(self):
        return self.user.name if self.user.name else self.user.username

class ZoomAccount(models.Model):
    account_id = models.CharField(max_length=100)
    client_id = models.CharField(max_length=100)
    client_secret = models.CharField(max_length=100)
    secret_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Zoom Account {self.id}"
    
    def is_available(self):
        """Check if this account is currently available"""
        # Check if there are any active temporary links using this account
        now = timezone.now()
        return not self.temporary_links.filter(
            link_valid_until__gt=now
        ).exists()
    
    @classmethod
    def get_available_account(cls):
        """Get an available Zoom account"""
        for account in cls.objects.all():
            if account.is_available():
                return account
        return None




# class ParentStudent(models.Model):
#     parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_students',
#                                limit_choices_to={'role': 'parent'})
#     student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_parents',
#                                 limit_choices_to={'role': 'student'})

#     def __str__(self):
#         return f"Parent: {self.parent.name} - Student: {self.student.name}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    age = models.IntegerField()

    def __str__(self):
        return f"{self.user.name}'s profile"



class TeacherInfo(models.Model):
    teacher = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_info', limit_choices_to={'role': 'teacher'})
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="A short description about the teacher.")
    specialization = models.CharField(max_length=100, blank=True, null=True, help_text="The teacher's area of expertise.")
    profile_link = models.URLField(max_length=200, blank=True, null=True, help_text="Link to the teacher's full profile.")
    is_active_to_be_shown_in_home = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.teacher.name}"


#------------------------translation models-----------------------#
class TeacherInfoTranslation(models.Model):
    teacher_info = models.ForeignKey(TeacherInfo, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_bio = models.TextField(max_length=500, blank=True, null=True)
    translated_specialization = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('teacher_info', 'language')

    def __str__(self):
        return f"{self.teacher_info.teacher.name} - {self.language}"

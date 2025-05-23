from django.db import models

from accounts.models import User
from courses.models import Course

# Create your models here.
class LibraryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Library Categories"

# Update CourseLibrary model
class CourseLibrary(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='libraries')
    file = models.FileField(upload_to='courseslibraries/')
    category = models.ForeignKey(LibraryCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='libraries')

    def __str__(self):
        return f"{self.course.name} | {self.file.name} | {self.category.name if self.category else 'Uncategorized'}"



class MyLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mylibraries' , limit_choices_to={'role': 'teacher'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mycourselibraries' , null=True , blank=True)
    file = models.FileField(upload_to='courseslibraries/')
    def __str__(self):
        return f"{self.user.username} | {self.course.name} | {self.file.name}"
    





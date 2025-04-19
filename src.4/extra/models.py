from django.db import models
from student.models import Year
# Create your models here.

class News(models.Model):
    text = models.TextField()
    year = models.ForeignKey(Year, on_delete=models.SET_NULL,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


class Update(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    text = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
import random
import string
from django.db import models
from django.conf import settings

def generate_unique_code():
    length = 8
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Room.objects.filter(code=code).exists():
            return code

class Room(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('opened', 'Opened'),
        ('finished', 'Finished'),
    ]
    code = models.CharField(max_length=8, unique=True, default=generate_unique_code)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)  # Allow null
    is_agent = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
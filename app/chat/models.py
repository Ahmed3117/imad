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
    
    # New fields for unread message tracking
    admin_unread_count = models.IntegerField(default=0)
    user_unread_count = models.IntegerField(default=0)
    
    def increment_admin_unread(self):
        """Increment the unread count for admin dashboard"""
        self.admin_unread_count += 1
        self.save(update_fields=['admin_unread_count'])
        
    def increment_user_unread(self):
        """Increment the unread count for user chat room"""
        self.user_unread_count += 1
        self.save(update_fields=['user_unread_count'])
        
    def reset_admin_unread(self):
        """Reset the admin unread count when an admin opens the room"""
        self.admin_unread_count = 0
        self.save(update_fields=['admin_unread_count'])
        
    def reset_user_unread(self):
        """Reset the user unread count when a user opens the room"""
        self.user_unread_count = 0
        self.save(update_fields=['user_unread_count'])

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_agent = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # No need to add a read status field as we're tracking counts at the room level
    
    def save(self, *args, **kwargs):
        """Override save to update unread counts"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only update counts for new messages
        if is_new:
            if self.is_agent:
                # If message is from agent, increment user unread count
                self.room.increment_user_unread()
            else:
                # If message is from user, increment admin unread count
                self.room.increment_admin_unread()
# models.py

import uuid
from django.db import models

from django.db.models import Sum, DecimalField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from accounts.models import User

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} by {self.student.username}"

    def calculate_total_price(self):
        for item in self.items.all():
            print(item)
        total_price = sum(item.content_object.final_price_after_discound for item in self.items.all())
        return total_price

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order.order_id} - {self.content_object}"



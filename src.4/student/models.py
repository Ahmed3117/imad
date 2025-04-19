import random
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Year(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return  f'{self.name}  - id: {self.id}'

class TypeEducation(models.Model):
    name = models.CharField(max_length=50)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return  f'{self.name}  - id: {self.id}'

class Student(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=50,blank=True, null=True)
    parent_phone = models.CharField(max_length=11,blank=True, null=True)
    type_education = models.ForeignKey(TypeEducation, null=True, on_delete=models.SET_NULL)
    year = models.ForeignKey(Year,null=True, on_delete=models.SET_NULL)
    points = models.IntegerField(default=1)
    division = models.CharField(max_length=50,blank=True, null=True)
    government = models.CharField(max_length=100,blank=True, null=True)
    jwt_token = models.CharField(max_length=1000, blank=True, null=True)
    active = models.BooleanField(default=False)
    block = models.BooleanField(default=False)
    code = models.CharField(max_length=50,blank=True, null=True)
    balance = models.IntegerField(default=0)
    by_code = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} | {self.id}'

class StudentCode(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    code = models.CharField(max_length=50,blank=True, null=True,unique=True)
    available = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.available} | {self.code}'

    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        while True:
            number = '00'+''.join(random.choices('0123456789', k=9))
            if not StudentCode.objects.filter(code=number).exists():
                return f'{number}'

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    device_name = models.CharField(max_length=255, default="Unknown")
    os_name = models.CharField(max_length=255, default="Unknown")
    browser_name = models.CharField(max_length=255)
    last_active = models.DateTimeField()
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} activity"
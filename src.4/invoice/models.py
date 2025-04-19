from django.db import models
from django.utils import timezone
from student.models import Student
from course.models import Course,CourseCollection,CourseCollectionCode,CourseCode,Lesson
import random
# Create your models here.

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expiration_date = models.DateTimeField(blank=True, null=True)
    usage_limit = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    used_by_students = models.ManyToManyField(Student ,blank=True, related_name="used_promo_codes")  
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_percent}% off"

    def is_valid(self):
        """Check if the promo code is active, not expired, and has remaining uses."""
        if not self.is_active:
            return False
        if self.expiration_date and timezone.now() > self.expiration_date:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True


class Invoice(models.Model):
    PAY_STATUS_CHOICES = [('P', 'غير مدفوع'),('C', 'مدفوع'),('F', 'فشل الدفع'),('E','انتهت الصلاحية')]
    PAY_METHOD_CHOICES = [
        ('M', 'يدوي'),
        ('C', 'كود'),
        ('F', 'فوري'),
        ('R', 'مجاني'),
        ('D', 'سنتر'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course,blank=True, null=True,on_delete=models.SET_NULL)
    course_collection = models.ForeignKey(CourseCollection,blank=True, null=True,on_delete=models.SET_NULL)
    lesson = models.ForeignKey(Lesson, blank=True, null=True, on_delete=models.SET_NULL)
    pay_status = models.CharField(max_length=1,choices=PAY_STATUS_CHOICES,default='P',)
    pay_method = models.CharField(max_length=1,choices=PAY_METHOD_CHOICES,default='M',)
    free = models.BooleanField(default=False)
    code = models.CharField(max_length=15,blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    sequence = models.CharField(max_length=14, unique=True, default='', blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)  
    pay_at = models.DateTimeField(blank=True, null=True)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, blank=True, null=True)
    fawry_reference_number = models.CharField(max_length=100,blank=True, null=True)
    fawry_signature = models.CharField(max_length=500,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invoice for {self.student.user.username} - {self.get_pay_status_display()}"
    
    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.sequence:
            self.sequence = self.generate_sequence()
        super().save(*args, **kwargs)
    
    def generate_sequence(self):
        while True:
            number = ''.join(random.choices('0123456789', k=14))
            if not Invoice.objects.filter(sequence=number).exists():
                return f'{number}'

    def is_expired(self):
        """Check if the invoice has expired and update the status if needed."""
        if self.expires_at and timezone.now() > self.expires_at:
            if self.pay_status != 'E':  # Update only if not already expired
                self.pay_status = 'E'
                self.save(update_fields=['pay_status'])
            return True
        return False


    def apply_promo_code(self):
        """Applies the promo code discount if a valid promo code is attached."""
        if self.promo_code and self.promo_code.is_valid():
            discount_amount = (self.price * self.promo_code.discount_percent) / 100
            self.price -= discount_amount
            # Increase promo code usage count
            self.promo_code.used_count += 1
            self.promo_code.save()


class BalanceTransaction(models.Model):
    TRANSACTION_TYPE = [
        ('A', 'اضافة'),
        ('D', 'خصم'),
        ('R', 'استرداد'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPE)
    code = models.CharField(max_length=50, blank=True, null=True) 
    note = models.TextField(blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} for {self.student.user.username}"
    

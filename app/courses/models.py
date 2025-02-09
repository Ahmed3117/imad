from django.db import models
# Levels Model
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP
from threading import local
from .middleware import get_current_request




class PricingMixin:
    def _is_egypt_request(self):
        request = get_current_request()
        if request is None:
            return False
        return getattr(request, 'is_egypt', False)

    def _quantize_price(self, price):
        if price is None:
            price = 0
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
        return price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class Level(models.Model, PricingMixin):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='levels/', default='defaults/default.jpg')
    preview_video = models.CharField(max_length=50, blank=True, null=True)
    year_limit = models.CharField(max_length=20)
    enable_pricing = models.BooleanField(default=True)
    egypt_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    @property
    def price_without_any_discount(self):
        is_egypt = self._is_egypt_request()
        individual_courses_price = self.courses.filter(track__isnull=True).aggregate(
            total=Sum('egypt_price' if is_egypt else 'price')
        )['total'] or 0

        track_courses_price = self.tracks.aggregate(
            total=Sum('courses__egypt_price' if is_egypt else 'courses__price')
        )['total'] or 0

        total_price = Decimal(individual_courses_price) + Decimal(track_courses_price)
        return self._quantize_price(total_price)

    @property
    def final_price_after_discound(self):
        total_price = self.price_without_any_discount
        if hasattr(self, 'discountlevel'):
            discount_percent = Decimal(self.discountlevel.discount_percent)
            total_price *= (Decimal(100) - discount_percent) / Decimal(100)
        return self._quantize_price(total_price)

    @property
    def has_discount(self):
        return hasattr(self, 'discountlevel')
    
    @property
    def discount_percent(self):
        return self.discountlevel.discount_percent if hasattr(self, 'discountlevel') else 0

    def __str__(self):
        return self.name

class Track(models.Model, PricingMixin):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='tracks/', default='defaults/default.jpg')
    preview_video = models.CharField(max_length=50, blank=True, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='tracks')
    egypt_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    @property
    def price_without_any_discount(self):
        is_egypt = self._is_egypt_request()
        total_price = self.courses.aggregate(
            total=Sum('egypt_price' if is_egypt else 'price')
        )['total'] or 0
        return self._quantize_price(total_price)

    @property
    def final_price_after_discound(self):
        total_price = self.price_without_any_discount
        if hasattr(self, 'discounttrack'):
            discount_percent = Decimal(self.discounttrack.discount_percent)
            total_price *= (Decimal(100) - discount_percent) / Decimal(100)
        return self._quantize_price(total_price)

    @property
    def has_discount(self):
        return hasattr(self, 'discounttrack')
    
    @property
    def discount_percent(self):
        return self.discounttrack.discount_percent if hasattr(self, 'discounttrack') else 0

    def __str__(self):
        return self.name

class Course(models.Model, PricingMixin):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    egypt_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='courses/', default='defaults/default.jpg')
    preview_video = models.CharField(max_length=50, blank=True, null=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='courses')
    track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')

    @property
    def price_without_any_discount(self):
        is_egypt = self._is_egypt_request()
        print(is_egypt)
        price = self.egypt_price if is_egypt else self.price
        return self._quantize_price(price)

    @property
    def final_price_after_discound(self):
        effective_price = self.price_without_any_discount
        
        try:
            discount = DiscountCourse.objects.get(course=self)
            discount_percent = Decimal(discount.discount_percent) if discount.discount_percent is not None else Decimal(0)
            effective_price *= (Decimal(100) - discount_percent) / Decimal(100)
        except DiscountCourse.DoesNotExist:
            pass
        
        return self._quantize_price(effective_price)

    @property
    def has_discount(self):
        return DiscountCourse.objects.filter(course=self).exists()
    
    @property
    def discount_percent(self):
        try:
            return DiscountCourse.objects.get(course=self).discount_percent
        except DiscountCourse.DoesNotExist:
            return 0
        
    def __str__(self):
        return self.name


class Session(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='coursesessions')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.course.name + " - " +self.title



class DiscountCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    discount_percent = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.course.name} - {self.discount_percent}% Discount"

class DiscountTrack(models.Model):
    track = models.OneToOneField(Track, on_delete=models.CASCADE)
    discount_percent = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.track.name} - {self.discount_percent}% Discount"

class DiscountLevel(models.Model):
    level = models.OneToOneField(Level, on_delete=models.CASCADE)
    discount_percent = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.level.name} - {self.discount_percent}% Discount"

class LevelContent(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE,related_name='contents')
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name



#-----------------------translation models-----------------------------#
class LevelTranslation(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('level', 'language')

    def __str__(self):
        return f"{self.level.name} - {self.language}"

class TrackTranslation(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('track', 'language')

    def __str__(self):
        return f"{self.track.name} - {self.language}"

class CourseTranslation(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('course', 'language')

    def __str__(self):
        return f"{self.course.name} - {self.language}"

class SessionTranslation(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_title = models.CharField(max_length=200)
    translated_content = models.TextField()

    class Meta:
        unique_together = ('session', 'language')

    def __str__(self):
        return f"{self.session.title} - {self.language}"

class LevelContentTranslation(models.Model):
    level_content = models.ForeignKey(LevelContent, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=200)

    class Meta:
        unique_together = ('level_content', 'language')

    def __str__(self):
        return f"{self.level_content.name} - {self.language}"


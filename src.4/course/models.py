import random
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
from student.models import Student , Year,TypeEducation
# Create your models here.

class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL,blank=True, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    cover = models.FileField(upload_to='covers', max_length=500,validators=[FileExtensionValidator(allowed_extensions=['png','jpg','jpeg','webp'])])
    promo_video = models.CharField(max_length=350,blank=True, null=True)
    time = models.IntegerField(default=0)
    free = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    center = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.name} | id : {self.id}'
    
    def get_units(self):
        return self.units.filter(pending=False)
    
    def get_lessons(self):
        return Lesson.objects.filter(unit__course=self, pending=False) 

    def get_discounted_price(self):
        """Calculate the price after applying the discount."""
        if self.discount > 0:
            discount_amount = (self.price * self.discount) / 100
            return max(0, self.price - discount_amount)
        return self.price


    def save(self, *args, **kwargs):
        # Only convert to WebP if the cover is not in the WebP format
        if self.cover and not self.cover.name.endswith('.webp'):
            try:
                # Open the image file and convert it to WebP format
                img = Image.open(self.cover)
                img = img.convert("RGB")  # Ensure compatibility with WebP

                webp_io = BytesIO()
                img.save(webp_io, format="WEBP", quality=85)

                # Create a new cover file with WebP extension
                webp_file = ContentFile(webp_io.getvalue())

                # Save the cover field with the WebP file
                self.cover.save(f"{self.cover.name.split('.')[0]}.webp", webp_file, save=False)

            except Exception as e:
                # Handle errors that might occur during image conversion
                print(f"Error converting image: {e}")
        
        # Call the save method once after all modifications
        super().save(*args, **kwargs)


class Unit(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    course = models.ForeignKey(Course, related_name='units', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)
    pending = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'unit-id : {self.id} | {self.name} | {self.course.name} [--{self.course.id}--] '

#*============================>Content Course<============================#*

class Lesson(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    unit = models.ForeignKey(Unit,related_name="unit_lessons", on_delete=models.CASCADE)
    view = models.IntegerField(default=5)
    video_views = models.IntegerField(default=0)
    video_duration = models.IntegerField(blank=True, null=True)
    video_url = models.CharField(max_length=250,blank=True, null=True)
    youtube_url =models.CharField(max_length=250,blank=True, null=True)
    vdocipher_id =models.CharField(max_length=250,blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    pending = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    is_plyr = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(f'{self.name} - id :{self.id}')

class LessonFile(models.Model):
    name = models.CharField(max_length=50,blank=True, null=True)
    lesson = models.ForeignKey(Lesson, related_name="lesson_files", on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='lessons/files/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'File for {self.lesson.name} - {self.file.name}'


class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='lessons/files/',validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    pending = models.BooleanField(default=False)
    unit = models.ForeignKey(Unit, related_name='files', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)
    # & Important
    # updated = models.DateTimeField(auto_now=True)
    # created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.name} - {self.unit.name}'


#*============================>Course Collection<============================#*

class CourseCollection(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.PositiveIntegerField(default=0)
    courses = models.ManyToManyField(Course, related_name='collections')
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    cover = models.FileField(upload_to='collections', max_length=500,validators=[FileExtensionValidator(allowed_extensions=['png','jpg','jpeg','webp'])])
    free = models.BooleanField(default=False)
    pending = models.BooleanField(default=False)
    center = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=5)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    


#*============================>Course Code<============================#*

class CourseCode(models.Model):
    title = models.CharField(max_length=50,blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    available = models.BooleanField(default=True)
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    code = models.CharField(max_length=14, unique=True, default='', blank=True, null=True)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.code:
            self.code = self.generate_code()
        if not self.price:
            self.price = self.course.price
        super().save(*args, **kwargs)
    
    def generate_code(self):
        while True:
            number = ''.join(random.choices('0123456789', k=8))
            if not CourseCode.objects.filter(code=number).exists():
                return f'{number}'


class CourseCollectionCode(models.Model):
    title = models.CharField(max_length=50,blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    available = models.BooleanField(default=True)
    collection = models.ForeignKey(CourseCollection,on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    code = models.CharField(max_length=14, unique=True, default='', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.code:
            self.code = self.generate_code()
        if not self.price:
            self.price = self.collection.price
        super().save(*args, **kwargs)
    
    def generate_code(self):
        while True:
            number = ''.join(random.choices('0123456789', k=8))
            if not CourseCode.objects.filter(code=number).exists():
                return f'{number}'

#*============================>Lesson Code<============================#*


class LessonCode(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    available = models.BooleanField(default=True)
    lesson = models.ForeignKey(Lesson,on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    code = models.CharField(max_length=14, unique=True, default='', blank=True, null=True)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generate a unique 14-digit number for sequence
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        while True:
            number = ''.join(random.choices('0123456789', k=14))
            if not LessonCode.objects.filter(code=number).exists():
                return f'{number}'


class AnyLessonCode(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE,blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson,on_delete=models.CASCADE,blank=True, null=True)
    available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    code = models.CharField(max_length=11,unique=True, default='', blank=True, null=True)
    updated  = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    
    def save(self, *args, **kwargs):
        # Generate a unique 11-digit number for sequence
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        while True:
            number = ''.join(random.choices('0123456789', k=11))
            if not AnyLessonCode.objects.filter(code=number).exists():
                return f'{number}'

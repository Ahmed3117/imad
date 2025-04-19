from rest_framework import serializers
from subscription.models import CourseSubscription,LessonSubscription
from .models import *


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    year__name=serializers.CharField(source='year.name')
    course_id = serializers.CharField(source='id')  
    discounted_price = serializers.SerializerMethodField()
    units_count = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()
    course_duration = serializers.SerializerMethodField()
    category__name = serializers.CharField(source='category.name', allow_null=True)
    
    class Meta:
        model = Course
        fields = [
            'course_id',
            'name',
            'description',
            'price',
            'discounted_price',
            'category',
            'category__name',
            'year__name',
            'cover',
            'promo_video',
            'units_count',
            'lessons_count',
            'files_count',
            'has_subscription',
            'course_duration',
            'center',
            'time',
            'free',
            'created'
        ]
    

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()

    def get_units_count(self, obj):
        return obj.units.filter(pending=False).count()

    def get_lessons_count(self, obj):
        return Lesson.objects.filter(unit__course=obj,pending=False).count()
    
    def get_files_count(self, obj):
        return File.objects.filter(unit__course=obj,pending=False).count()

    def get_course_duration(self, obj):
        duration = 0
        lessons = Lesson.objects.filter(unit__course=obj,pending=False)
        for lesson in lessons:
            if lesson.video_duration:
                duration+=lesson.video_duration
        return duration


    def get_has_subscription(self, obj):
        # Get the request from the serializer context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if the student is subscribed to the course
            student = request.user.student
            return CourseSubscription.objects.filter(student=student, course=obj, active=True).exists()
        return False


class UnitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Unit
        fields = [
            'id',
            'name',
            'description',
            'course',
            'order',
            'created'
        ]


class LessonFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonFile
        fields = ['id', 'name', 'file', 'created']

class LessonSerializer(serializers.ModelSerializer):
    lesson_files_count = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()
    class Meta:
        model = Lesson
        fields = [
            'id',
            'name',
            'description',
            'unit',
            'view',
            'order',
            'video_duration',
            'created',
            'lesson_files_count',
            'is_plyr',
            'points',
            'has_subscription',
        ]

    def get_lesson_files_count(self, obj):
        return obj.lesson_files.count()  

    def get_has_subscription(self, obj):
        # Get the request from the serializer context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if the student is subscribed to the course
            student = request.user.student
            
            return LessonSubscription.objects.filter(student=student, lesson=obj, active=True).exists()
        return False
    


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id', 
            'name', 
            'order',
            ]

#*============================>Course Collection<============================#*

class CourseCollectionSerializer(serializers.ModelSerializer):
    year_name = serializers.CharField(source='year.name', read_only=True)
    course_collection_id = serializers.IntegerField(source='id', read_only=True)
    course_count = serializers.SerializerMethodField()
    courses = CourseSerializer(many=True, source='course')

    class Meta:
        model = CourseCollection
        fields = [
            'course_collection_id',
            'name',
            'description',
            'price',
            'year_name',
            'cover',
            'course_count',
            'free',
            'center',
            'pending',
            'created',
            'courses',
        ]

    def get_course_count(self, obj):
        """Return the count of related courses."""
        return obj.course.count()

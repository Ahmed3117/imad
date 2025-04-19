from rest_framework import serializers
from course.models import *
from subscription.models import CourseSubscription

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = '__all__'


class CreateCourseSerializers(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=CourseCategory.objects.all(), required=False, allow_null=True)
    class Meta:
        model = Course
        fields=[
            'name',
            'description',
            'price',
            'discount',
            'year',
            'cover',
            'promo_video',
            'free',
            'pending',
            'center',
            'category'
        ]


class UpdateCourseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    year = serializers.PrimaryKeyRelatedField(queryset=Year.objects.all(), required=False, allow_null=True)
    cover = serializers.FileField(required=False, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=CourseCategory.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Course
        fields = [
            'name',
            'description',
            'price',
            'discount',
            'year',
            'cover',
            'promo_video',
            'free',
            'pending',
            'center',
            'category'
        ]


class ListCourseSerializer(serializers.ModelSerializer):
    units_count = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    in_course_count = serializers.SerializerMethodField()
    year__name = serializers.CharField(source='year.name')
    category__name = serializers.CharField(source='category.name', allow_null=True)
    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'description',
            'price',
            'discount',
            'year__name',
            'year',
            'cover',
            'category',
            'category__name',
            'promo_video',
            'time',
            'free',
            'pending',
            'center',
            'units_count',
            'lessons_count',
            'files_count',
            'in_course_count',
            'created',

        ]

    def get_units_count(self, obj):
        return obj.units.all().count()
    
    def get_lessons_count(self, obj):
        return Lesson.objects.filter(unit__course=obj).count()
    
    def get_files_count(self, obj):
        return File.objects.filter(unit__course=obj).count()
    
    def get_in_course_count(self, obj):
        return CourseSubscription.objects.filter(course=obj).count()



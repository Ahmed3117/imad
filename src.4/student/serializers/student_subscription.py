from rest_framework import serializers
from subscription.models import *
from course.models import *

class ListCourseSubscriptionSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="student.user.username")
    student__name = serializers.CharField(source="student.name")
    invoice_sequence = serializers.CharField(source="invoice.sequence",allow_null=True)
    invoice_method = serializers.CharField(source="invoice.pay_method",allow_null=True)
    course_id = serializers.CharField(source='course.id')  
    course__name = serializers.CharField(source="course.name")
    course__cover = serializers.CharField(source="course.cover.url")
    course__description = serializers.CharField(source="course.description")
    units_course_count = serializers.SerializerMethodField()
    lessons_course_count = serializers.SerializerMethodField()
    files_course_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseSubscription
        fields = [
            'id',
            'user__username',
            'student__name',
            'invoice_sequence',
            'invoice_method',
            'course_id',
            'course__name',
            'course__cover',
            'course__description',
            'units_course_count',
            'lessons_course_count',
            'files_course_count',
            'active',
            'created',
        ]
    
    def get_units_course_count(self, obj):
        return obj.course.units.filter(pending=False).count()

    def get_lessons_course_count(self, obj):
        return Lesson.objects.filter(unit__course=obj.course,pending=False).count()
    
    def get_files_course_count(self, obj):
        return File.objects.filter(unit__course=obj.course,pending=False).count()


class ListLessonSubscriptionSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="student.user.username")
    lesson__name = serializers.CharField(source="lesson.name")
    student__name = serializers.CharField(source="student.name")
    invoice_sequence = serializers.CharField(source="invoice.sequence",allow_null=True)
    invoice_method = serializers.CharField(source="invoice.pay_method",allow_null=True)
    lesson_id = serializers.CharField(source='lesson.id')  
    course__name = serializers.CharField(source="lesson.unit.course.name")

    class Meta:
        model = LessonSubscription
        fields = [
            'id',
            'lesson__name',
            'user__username',
            'student__name',
            'invoice_sequence',
            'invoice_method',
            'lesson_id',
            'course__name',
        ]
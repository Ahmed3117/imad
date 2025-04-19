from rest_framework import serializers
from subscription.models import *
from view.models import *

class StudentLessonViewList(serializers.ModelSerializer):
    lesson__name = serializers.CharField(source="lesson.name")
    lesson_view = serializers.CharField(source="lesson.view")
    course_name = serializers.CharField(source="lesson.unit.course.name")
    class Meta:
        model = LessonView
        fields=[
            'id',
            'lesson',
            'lesson__name',
            'lesson_view',
            'course_name',
            'counter',
            'total_watch_time',
            'updated',
            'created',
        ]
    
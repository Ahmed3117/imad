from rest_framework import serializers
from course.models import LessonCode

class LessonCodeSerializer(serializers.ModelSerializer):
    lesson__name = serializers.CharField(source="lesson.name")
    student__name = serializers.CharField(source="student.name", allow_null=True)
    lesson_id = serializers.CharField(source="lesson.id")
    
    class Meta:
        model = LessonCode
        fields = [
            'id', 
            'student', 
            "student__name",
            'lesson',
            "lesson__name",
            "lesson_id",
            'price', 
            'code',
            'available',
        ]
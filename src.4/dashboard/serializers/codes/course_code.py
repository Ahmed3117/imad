from rest_framework import serializers
from course.models import CourseCode

class CourseCodeSerializer(serializers.ModelSerializer):
    course__name = serializers.CharField(source="course.name")
    student__name = serializers.CharField(source="student.name",allow_null=True)
    student__username = serializers.CharField(source="student.user.username",allow_null=True)
    class Meta:
        model = CourseCode
        fields = [
            'id', 
            'title', 
            'student',
            'student__name',
            'student__username',
            'course',
            "course__name",
            'price', 
            'code',
            'available'
        ]
from rest_framework import serializers
from course.models import *
from view.models import *

class ListLessonViewListSerializer(serializers.ModelSerializer):
    lesson_name = serializers.CharField(source="lesson.name")  
    student_id = serializers.CharField(source="student.id") 
    student_name = serializers.CharField(source="student.name")  
    student_username = serializers.CharField(source="student.user.username")  

    class Meta:
        model = LessonView
        fields = [
            'id',
            'lesson_name', 
            'student_id',
            'student_name', 
            'student_username',
            'total_watch_time',
            'counter'
            ] 
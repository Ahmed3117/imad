from rest_framework import serializers
from analysis.models import StudentPoint
from course.models import Lesson

class StudentPointSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id')
    student_name = serializers.CharField(source='student.name')
    student_number = serializers.CharField(source='student.user.username')
    student_code = serializers.CharField(source='student.code')
    class Meta:
        model = StudentPoint
        fields = '__all__'

class ListLessonVideoSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='unit.course.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'name', 'description', 'unit', 'view', 'video_views', 
            'video_duration', 'video_url', 'youtube_url', 'vdocipher_id', 
            'order', 'pending', 'ready', 'points', 'updated', 'created',
            'course_name', 'unit_name'
        ]
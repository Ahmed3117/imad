from rest_framework import serializers
from subscription.models import *
from course.models import *
from view.admin import LessonView

class LessonFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonFile
        fields = ['id', 'name', 'file', 'created']



class LessonSerializerSubscriptions(serializers.ModelSerializer):
    exam = serializers.SerializerMethodField()
    lesson_files = LessonFileSerializer(many=True, read_only=True)
    is_encrypt = serializers.SerializerMethodField()
    has_watched = serializers.SerializerMethodField()
    class Meta:
        model = Lesson
        fields = [
            'id',
            'name',
            'is_encrypt',
            'description',
            'video_duration',
            'unit',
            'view',
            'has_watched',
            'points',
            'order',
            'exam',
            'lesson_files',
            'is_plyr',
            ]
        
    def get_exam(self, obj):
        # Get the first exam associated with the lesson, if it exists
        exam = obj.exams.first()
        if exam:
            return {
                'id': exam.id,
                'name': exam.title,
            }
        return None
    
    def get_is_encrypt(self, obj):
        if obj.video_url:
            return True
        return False

    def get_has_watched(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            student = getattr(request.user, 'student', None)
            if student:
                return LessonView.objects.filter(lesson=obj, student=student,counter__gte=1).exists()
        return False


class AccessLessonSerializer(serializers.ModelSerializer):
    exam = serializers.SerializerMethodField()
    lesson_files = LessonFileSerializer(many=True, read_only=True)
    has_watched = serializers.SerializerMethodField()
    class Meta:
        model = Lesson
        fields = [
            'id',
            'youtube_url',
            'vdocipher_id',
            'name',
            'description',
            'video_duration',
            'unit',
            'view',
            'lesson_files',
            'has_watched',
            'order',
            'exam',
            'is_plyr',
            ]

    def get_exam(self, obj):
        # Get the first exam associated with the lesson, if it exists
        exam = obj.exams.first()
        if exam:
            return {
                'id': exam.id,
                'name': exam.title,
            }
        return None
    
    def get_has_watched(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            student = getattr(request.user, 'student', None)
            if student:
                return LessonView.objects.filter(lesson=obj, student=student,counter__gte=1).exists()
        return False



class AccessFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'id',
            'name',
            'file',
            'unit',
            'order',
            ]





from rest_framework import serializers
from course.models import *

class FileLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonFile
        fields = '__all__'


class ListLessonSerializer(serializers.ModelSerializer):
    lesson_files = FileLessonSerializer(many=True, read_only=True)
    class Meta:
        model = Lesson
        fields = '__all__'


class CreateLessonSerializer(serializers.ModelSerializer):
    lesson_files = FileLessonSerializer(many=True, required=False)

    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['unit']

    def create(self, validated_data):
        lesson_files_data = validated_data.pop('lesson_files', [])
        
        lesson = Lesson.objects.create(**validated_data)

        # Ensure correct file handling
        for file_data in lesson_files_data:
            LessonFile.objects.create(lesson=lesson, file=file_data['file'])

        return lesson


class UpdateLessonSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all(), required=False)
    description = serializers.CharField(required=False)
    class Meta:
        model = Lesson
        fields = '__all__'



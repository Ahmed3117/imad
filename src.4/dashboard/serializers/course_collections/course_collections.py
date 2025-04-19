from rest_framework import serializers
from course.models import CourseCollection


class CourseCollectionListSerializer(serializers.ModelSerializer):
    courses = serializers.StringRelatedField(many=True) 

    class Meta:
        model = CourseCollection
        fields = ['id', 'name', 'description', 'price', 'free', 'pending', 'center', 'points', 'start_date', 'end_date', 'updated', 'created', 'courses','cover','year']


class CourseCollectionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCollection
        fields = '__all__'
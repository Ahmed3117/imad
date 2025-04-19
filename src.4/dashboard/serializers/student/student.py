from django.contrib.auth.models import User
from django.db.models import F, Count
from rest_framework import serializers
from student.models import *

class StudentSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="user.username")
    type_education__name = serializers.CharField(source="type_education.name")
    year__name = serializers.CharField(source="year.name")
    #rank = serializers.SerializerMethodField()
    student_course_count = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = [
            'id',
            'user__username',
            'name',
            'parent_phone',
            'division',
            'type_education',
            'type_education__name',
            'year',
            'points',
            'year__name',
            'government',
            'code',
            'jwt_token',
            'by_code',
            'active',
            'block',
            'points',
            #'rank',
            'student_course_count',
            'is_admin',
            'created'
        ]

    # def get_rank(self, obj):
    #     rank = (
    #         Student.objects.filter(points__gt=obj.points)
    #         .annotate(rank=Count('id'))
    #         .count()
    #     ) + 1
    #     return rank

    def get_student_course_count(self,obj):
        return obj.coursesubscription_set.filter(active=True).count()

class UpdateStudentSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source='user.username' ,required=False, allow_blank=True)
    name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    parent_phone = serializers.CharField(max_length=11, required=False, allow_blank=True)
    type_education = serializers.PrimaryKeyRelatedField(queryset=TypeEducation.objects.all(), required=False)
    year = serializers.PrimaryKeyRelatedField(queryset=Year.objects.all(), required=False)
    government = serializers.CharField(max_length=100, required=False, allow_blank=True)
    active = serializers.BooleanField(required=False)
    block = serializers.BooleanField(required=False)
    by_code = serializers.BooleanField(required=False)
    is_admin = serializers.BooleanField(required=False)

    class Meta:
        model = Student
        fields = [
        'user__username', 
        'name', 'parent_phone', 
        'type_education', 
        'year', 'government',
        'active', 'block',
        'code', 
        'by_code', 'is_admin',]


    def update(self, instance, validated_data):
        # Update the user object (username)
        user_data = validated_data.pop('user', None)
        if user_data:
            username = user_data.get('username', None)
            if username:
                instance.user.username = username
                instance.user.save()


        # Handle the rest of the Student fields update
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the updated Student instance
        instance.save()
        return instance


from django.contrib.auth.models import User
from django.db.models import F, Count
from rest_framework import serializers
from student.models import *

class StudentProfileSerializer(serializers.ModelSerializer):
    user__username = serializers.CharField(source="user.username")
    type_education__name = serializers.CharField(source="type_education.name")
    year__name = serializers.CharField(source="year.name")
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'user__username',
            'name',
            'parent_phone',
            'type_education',
            'type_education__name',
            'year',
            'year__name',
            'government',
            'code',
            'points',
            'rank',
            'division',
            'by_code',
            'active',
            'block',
            'is_admin'
        ]

        read_only_fields = [
            "code",
            "by_code",
            "active",
            "block",
            "is_admin",
        ]


    def get_rank(self, obj):
        rank = (
            Student.objects.filter(points__gt=obj.points)
            .annotate(rank=Count('id'))
            .count()
        ) + 1
        return rank


class StudentSignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=True)
    password = serializers.CharField(source='user.password', write_only=True, required=True)
    email = serializers.EmailField(source='user.email', required=False)  # Email is optional
    parent_phone = serializers.CharField(required=False)

    class Meta:
        model = Student
        fields = [
            'username', 'password', 'email',  
            'name', 'parent_phone', 'type_education',
            'division',
            'year', 'government', 
        ]

    def validate(self, data):
        # Ensure username is not equal to parent_phone
        username = data['user']['username']
        parent_phone = data.get('parent_phone')

        if parent_phone and username == parent_phone:
            # Raise the error associated with the 'username' field
            raise serializers.ValidationError({"username": "Username cannot be the same as parent phone."})

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})
        
        return data

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student

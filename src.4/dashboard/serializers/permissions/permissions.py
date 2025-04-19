from rest_framework import serializers
from django.contrib.auth.models import Permission,User

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['codename', 'name']



class UserWithPermissionSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(source='user_permissions', many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'permissions']
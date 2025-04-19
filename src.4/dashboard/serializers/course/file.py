from rest_framework import serializers
from course.models import *

class ListFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class CreateFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['unit']



class UpdateFileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    file = serializers.FileField(required=False)
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all(), required=False)
    class Meta:
        model = File
        fields = '__all__'

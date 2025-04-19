from rest_framework import serializers
from course.models import *

class ListUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


class CreateUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'
        read_only_fields = ['course'] 


class UpdateUnitSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False)
    description = serializers.CharField(required=False)
    class Meta:
        model = Unit
        fields = '__all__'

from rest_framework import serializers
from .models import *

class NewsSerializer(serializers.ModelSerializer):
    year = serializers.PrimaryKeyRelatedField(queryset=Year.objects.all(), allow_null=True)

    class Meta:
        model = News
        fields = ['id', 'text', 'year', 'updated', 'created']



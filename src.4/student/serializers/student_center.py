from rest_framework import serializers
from desktop_app.models import ResultExamCenter,Attendance

class ResultExamCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultExamCenter
        fields = [
            'name',
            'lecture',
            'date',
            'result_photo',
            'result_percentage',
        ]


class AttendanceCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultExamCenter
        fields = '__all__'
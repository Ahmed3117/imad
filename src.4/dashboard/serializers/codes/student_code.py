from rest_framework import serializers
from student.models import StudentCode

class StudentCodeSerializer(serializers.ModelSerializer):
    student__username = serializers.CharField(source='student.user.username', allow_null=True )
    class Meta:
        model = StudentCode
        fields = [
            'id', 
            'code', 
            'available', 
            'student__username',
        ]


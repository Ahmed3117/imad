from rest_framework import serializers
from course.models import *
from subscription.models import CourseSubscription

class ListStudentCourseSubscription(serializers.ModelSerializer):
    student_id = serializers.CharField(source="student.id")
    student__name = serializers.CharField(source="student.name")
    student__user__username = serializers.CharField(source="student.user.username")
    course__name = serializers.CharField(source="course.name")
    student__government = serializers.CharField(source="student.government")
    student__parent_phone = serializers.CharField(source="student.parent_phone")
    invoice__sequence = serializers.CharField(source="invoice.sequence",allow_null=True)
    class Meta:
        model = CourseSubscription
        fields = [
            'id',
            'student_id',
            'student__name',
            'student__user__username',
            'student__government',
            'student__parent_phone',
            'course__name',
            'active',
            'invoice__sequence',
            'created'
        ]
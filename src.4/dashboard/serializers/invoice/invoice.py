from rest_framework import serializers
from invoice.models import Invoice

class ListInvoiceSerializer(serializers.ModelSerializer):
    course__name = serializers.CharField(source="course.name", allow_null=True)
    course__price = serializers.CharField(source="course.price", allow_null=True)
    course_collection__name = serializers.CharField(source="course_collection.name", default=False, allow_null=True)
    course_collection__price = serializers.CharField(source="course_collection.price", default="0", allow_null=True)
    lesson__name = serializers.CharField(source="lesson.name", allow_null=True)
    lesson__price = serializers.CharField(source="lesson.price", allow_null=True)
    student__name = serializers.CharField(source="student.name")
    student__username = serializers.CharField(source="student.user.username")
    promo_code__code = serializers.CharField(source='promo_code.code', default=None)
    promo_code__discount_percent = serializers.CharField(source='promo_code.discount_percent', default='0')

    class Meta:
        model = Invoice
        fields = [
            'id',
            'course',
            'course__name',
            'course__price',
            'course_collection__name',
            'course_collection__price',
            'lesson__name',
            'lesson__price',
            'student__name',
            'student__username',
            'pay_status',
            'pay_method',
            'free',
            'code',
            'price',
            'sequence',
            'expires_at',
            'promo_code__code',
            'promo_code__discount_percent',
            'created',
        ]


class UpdateInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['pay_status']

    def validate_pay_status(self, value):
        if value not in ["C"]:  
            raise serializers.ValidationError("Invalid pay_status value.")
        return value
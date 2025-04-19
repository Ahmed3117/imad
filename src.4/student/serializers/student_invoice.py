from rest_framework import serializers
from invoice.models import Invoice, PromoCode

class StudentInvoiceSerializer(serializers.ModelSerializer):
    course__name = serializers.CharField(source="course.name", allow_null=True)
    course__price = serializers.CharField(source="course.price", allow_null=True)
    course_collection__name = serializers.CharField(source="course_collection.name",  allow_null=True)
    course_collection__price = serializers.CharField(source="course_collection.price", allow_null=True)
    lesson__name = serializers.CharField(source="lesson.name", allow_null=True)
    lesson__price = serializers.CharField(source="lesson.price", allow_null=True)
    promo_code__code = serializers.CharField(source='promo_code.code',default=None)
    promo_code__discount_percent = serializers.CharField(source='promo_code.discount_percent',default='0')
    
    class Meta:
        model = Invoice
        fields = [
            'course__name',
            'course__price',
            'course_collection__name',
            'course_collection__price',
            'lesson__name',
            'lesson__price',
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

from rest_framework import serializers
from invoice.models import PromoCode

class ListPromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = [
            'code',
            'course',
            'discount_percent',
            'expiration_date',
            'usage_limit',
            'is_active',
        ]







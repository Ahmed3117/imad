from django_filters import rest_framework as filters
from django.utils import timezone
from invoice.models import Invoice
from .models import RequestLog
import django_filters
import datetime


class InvoiceFilter(django_filters.FilterSet):
    created = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Invoice
        fields = ['course', 'pay_status', 'pay_method', 'free', 'created']



#^---------------------logs-----------------

class RequestLogFilter(filters.FilterSet):
    timestamp_after = filters.DateFilter(field_name='timestamp', lookup_expr='gte', method='filter_timestamp_after')
    timestamp_before = filters.DateFilter(field_name='timestamp', lookup_expr='lte', method='filter_timestamp_before')
    
    def filter_timestamp_after(self, queryset, name, value):
        # Convert date to datetime with time set to 00:00:00
        start_datetime = timezone.make_aware(datetime.datetime.combine(value, datetime.time.min))
        return queryset.filter(timestamp__gte=start_datetime)
    
    def filter_timestamp_before(self, queryset, name, value):
        # Convert date to datetime with time set to 23:59:59
        end_datetime = timezone.make_aware(datetime.datetime.combine(value, datetime.time.max))
        return queryset.filter(timestamp__lte=end_datetime)
    
    class Meta:
        model = RequestLog
        fields = {
            'user': ['exact'],
            'method': ['exact'],
            'status_code': ['exact'],
            'path': ['icontains'],
            'timestamp': ['exact'],  
        }


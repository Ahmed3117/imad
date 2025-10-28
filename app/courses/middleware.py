from threading import local
import requests
from django.core.cache import cache

from project import settings

_thread_locals = local()

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response

class LocationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Try to get country from cache first
        cache_key = f'country_code_{ip_address}'
        is_egypt = cache.get(cache_key)
        
        if is_egypt is None:
            is_egypt = self.is_egyptian_ip(ip_address)
            # Cache the result for 24 hours
            cache.set(cache_key, is_egypt, 60 * 60 * 24)
        
        request.is_egypt = is_egypt
        return self.get_response(request)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_egyptian_ip(self, ip):
        # # In LocationMiddleware.is_egyptian_ip
        # if settings.DEBUG and ip in getattr(settings, 'INTERNAL_IPS', []):
        #     return True  # Always treat development IPs as Egyptian
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            data = response.json()
            return data.get('countryCode') == 'EG'
        except Exception as e:
            print(f"Error detecting country: {e}")
            return False  # Default to non-Egyptian pricing if detection fails
        


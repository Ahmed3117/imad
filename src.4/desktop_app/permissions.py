from rest_framework.permissions import BasePermission
from django.conf import settings

class HasValidAPIKey(BasePermission):

    def has_permission(self, request, view):
        api_key = request.headers.get("api-key")
        valid_api_key = settings.API_KEY_DESKTOP

        return api_key == valid_api_key
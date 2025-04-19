import json
import time
from .models import RequestLog
from django.utils.deprecation import MiddlewareMixin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.http import HttpResponseServerError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView

import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()

class ActionLoggingMiddleware(MiddlewareMixin):
    def get_user_from_jwt(self, request):
        """Extract user from JWT token in Authorization header."""
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            jwt_auth = JWTAuthentication()
            try:
                validated_token = jwt_auth.get_validated_token(token)
                user = jwt_auth.get_user(validated_token)
                return user if user.is_staff else None  # Only allow staff users
            except Exception as e:
                if settings.DEBUG:
                    print(f"JWT Parsing Error: {e}")
        return None

    def get_model_name(self, request):
        """Extract the actual model name from the view's serializer."""
        try:
            view = request.resolver_match.func.view_class
            if issubclass(view, GenericAPIView) and hasattr(view, "serializer_class"):
                return view.serializer_class.Meta.model._meta.model_name  # Extract model name
        except Exception as e:
            if settings.DEBUG:
                print(f"Error extracting model name: {e}")
        return None

    def process_request(self, request):
        """Store request body before modifying it."""
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                request._body_data = request.body.decode("utf-8")  # Decode as UTF-8
            except UnicodeDecodeError:
                request._body_data = None  # Handle binary data safely

    def process_response(self, request, response):
        """Log actions only if the user is staff and for specific requests."""
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return response

        # Ensure the user is authenticated and staff
        user = request.user if request.user.is_authenticated and request.user.is_staff else self.get_user_from_jwt(request)
        if not user:
            return response  # Skip logging if the user is not staff

        model_name = self.get_model_name(request)
        if not model_name:
            return response  # Skip logging if model name is not found

        try:
            data = json.loads(request._body_data) if request._body_data else {}

            if request.method == "POST":
                action_flag = ADDITION
                action_message = "Created"
            elif request.method in ["PUT", "PATCH"]:
                action_flag = CHANGE
                action_message = "Updated"
            elif request.method == "DELETE":
                action_flag = DELETION
                action_message = "Deleted"
            else:
                return response

            # Log the action
            LogEntry.objects.log_action(
                user_id=user.id,
                content_type_id=ContentType.objects.get(model=model_name).id,
                object_id=data.get("id", None),
                object_repr=str(data),
                action_flag=action_flag,
                change_message=f"{action_message} object: {data}",
            )
        except Exception as e:
            if settings.DEBUG:
                print(f"Logging Middleware Error: {e}")

        return response

class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        if response is None:
            return HttpResponseServerError("Internal Server Error")

        # Paths to exclude from logging
        exclude_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/dashboard/logs/',
            '/dashboard/logs/delete/',
        ]
        if any(request.path.startswith(path) for path in exclude_paths):
            return response

        # ✅ Only log requests from staff users
        if not request.user.is_authenticated or not request.user.is_staff:
            return response

        # ✅ Ignore GET requests
        if request.method == "GET":
            return response

        # Response time calculation
        response_time_ms = (time.time() - getattr(request, 'start_time', time.time())) * 1000

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        # Get query parameters (JSON format)
        query_params = dict(request.GET)

        # Determine the view name
        view_name = None
        if hasattr(response, 'renderer_context') and response.renderer_context:
            view = response.renderer_context.get('view')
            if view:
                view_name = f"{view.__class__.__module__}.{view.__class__.__name__}"

        # Log request
        try:
            RequestLog.objects.create(
                user=request.user,
                ip_address=ip_address,
                path=request.path,
                method=request.method,
                view_name=view_name,
                query_params=query_params,
                status_code=response.status_code,
                response_time=response_time_ms
            )
        except Exception as e:
            print(f"Error logging request: {e}")

        return response





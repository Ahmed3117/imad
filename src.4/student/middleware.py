from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import Student

class StudentBlockMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth = JWTAuthentication()
        try:
            user, token = auth.authenticate(request)
            if user and hasattr(user, 'student') and user.student.block:
                # Blacklist the token to log out the user
                try:
                    BlacklistedToken.objects.create(token=OutstandingToken.objects.get(token=token))
                except OutstandingToken.DoesNotExist:
                    pass  # Token might not be stored in OutstandingToken

                return JsonResponse({"Error": "Student Blocked, Logged Out"}, status=403)
        except:
            return None
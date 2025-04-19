# RestFrameWork lib
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, filters
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from .models import Notification
# Create your views here.

class NotificationReadUpdate(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self,request,*args, **kwargs):
        get_student = request.user.student
        filter_notify = Notification.objects.filter(student=get_student).update(is_read=True)

        return Response(status=status.HTTP_200_OK)
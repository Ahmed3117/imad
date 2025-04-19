from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from student.models import Student
from course.models import Course
from .models import *
from .serializers import NewsSerializer
# Create your views here.


class NewsListAPIView(generics.ListAPIView):
    serializer_class = NewsSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            student_year = self.request.user.student.year
            return News.objects.filter(year=student_year).order_by("-created")
        return News.objects.all()
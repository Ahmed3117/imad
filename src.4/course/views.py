from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework.filters import SearchFilter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from exam.serializers import *
from .models import *
from .serializers import *


class CourseCategoryListView(generics.ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']


class CourseListView(generics.ListAPIView):
    serializer_class = CourseSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['year','category']
    search_fields = ['name']

    def get_queryset(self):
        # Base queryset
        queryset = Course.objects.filter(pending=False, center=False)

        # Apply filters if the user is authenticated
        if self.request.user.is_authenticated:
            student = self.request.user.student
            year = student.year
            filters = {'pending': False, 'year': year}

            # Adjust filters based on `by_code`
            if not student.by_code:
                filters['center'] = False

            queryset = Course.objects.filter(**filters)

        return queryset.order_by("-created")


    def get_serializer_context(self):
        # Pass the request to the serializer context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    
    def list(self, request, *args, **kwargs):
        # Get the original response
        response = super().list(request, *args, **kwargs)

        # Add `course_content_url` to each course object
        for course in response.data:
            course['course_content_url'] = f'{settings.FRONT_BASE_URL}/user-profile/course-content/{course["course_id"]}'

        return response


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()  # Base queryset
    serializer_class = CourseSerializer
    lookup_field = 'id'  # Default is 'pk', you can change it if needed

    def get_queryset(self):
        # Base queryset
        queryset = Course.objects.filter(center=False)

        # Apply filters if the user is authenticated
        if self.request.user.is_authenticated:
            student = self.request.user.student
            year = student.year
            filters = {'year': year}

            # Adjust filters based on `by_code`
            if not student.by_code:
                filters['center'] = False

            queryset = Course.objects.filter(**filters)

        return queryset

    def get_serializer_context(self):
        # Pass the request to the serializer context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class UnitListView(generics.ListAPIView):
    serializer_class = UnitSerializer
    pagination_class = None 
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Unit.objects.filter(course_id=course_id,pending=False).order_by("order")
    

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class UnitContent(APIView):
    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id)
        content = self.get_content(unit)

        return Response(content, status=status.HTTP_200_OK)

    def get_content(self, unit):
        lessons = self.get_lessons(unit)
        files = self.get_files(unit)
        exams = self.get_exams(unit)

        # Combine lessons, files, and exams into a unified list
        combined_content = self.combine_content(lessons, files, exams)

        return combined_content

    def get_lessons(self, unit):
        lessons = unit.unit_lessons.filter(pending=False)
        return LessonSerializer(lessons, many=True,context={'request': self.request}).data

    def get_files(self, unit):
        files = unit.files.filter(pending=False)
        return FileSerializer(files, many=True).data

    def get_exams(self, unit):
        exams = unit.exams.filter(is_active=True)
        return ExamSerializer(exams, many=True).data

    def combine_content(self, lessons, files, exams):
        combined_content = sorted(
            [{'content_type': 'lesson', **lesson} for lesson in lessons] +
            [{'content_type': 'file', **file} for file in files] +
            [{'content_type': 'exam', **exam} for exam in exams],
            key=lambda x: x.get('order', 0)
        )
        return combined_content


#*============================>Course Collection<============================#*


class CourseCollectionListView(generics.ListAPIView):
    serializer_class = CourseCollectionSerializer
    pagination_class = None

    def get_queryset(self):
        # Base queryset
        queryset = CourseCollection.objects.filter(pending=False)

        # Apply filters if the user is authenticated
        if self.request.user.is_authenticated:
            student = self.request.user.student
            year = student.year
            queryset = CourseCollection.objects.filter(year=year, pending=False)

        return queryset.order_by("-created")

    def get_serializer_context(self):
        # Pass the request to the serializer context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
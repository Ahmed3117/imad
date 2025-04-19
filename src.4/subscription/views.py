import requests
# DJANGO LIB
from django.http import HttpRequest
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import F, OuterRef, Subquery, Exists
#REST LIB
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
# Models
from course.models import *
from view.models import *
from .models import *
from exam.models import Exam, ResultTrial
# Serializers
from .serializers import *
from exam.serializers import *
# Utils
from .utils import *
# Create your views here.


class UnitContentSubscription(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id)
        student = request.user.student
        if not CourseSubscription.objects.filter(student=student, course=unit.course, active=True).exists():
            return Response({"error": "You do not have access permissions"}, status=status.HTTP_401_UNAUTHORIZED)

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
        return LessonSerializerSubscriptions(lessons, many=True,context={'request': self.request}).data

    def get_files(self, unit):
        files = unit.files.filter(pending=False)
        return AccessFileSerializer(files, many=True).data

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


class AccessContent(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, content_type, content_id, *args, **kwargs):
        course = get_object_or_404(Course, id=course_id)
        student = request.user.student

        if not self._has_active_subscription(student, course):
            return Response({"error": "You do not have access permissions"}, status=status.HTTP_401_UNAUTHORIZED)

        access_methods = {
            "lesson": self._access_lesson,
            "file": self._access_file,
        }
        
        access_method = access_methods.get(content_type)
        if not access_method:
            return Response({"error": "Invalid content type"}, status=status.HTTP_400_BAD_REQUEST)
        
        return access_method(course, content_id, student)

    def _has_active_subscription(self, student, course):
        return CourseSubscription.objects.filter(student=student, course=course, active=True).exists()

    def _access_lesson(self, course, lesson_id, student):
        lesson = get_object_or_404(Lesson, id=lesson_id)

        if lesson.unit.course != course:
            return Response({"error": "This lesson does not belong to the specified course"}, status=status.HTTP_400_BAD_REQUEST)
        if lesson.pending:
            return Response({"error": "This lesson is pending and unavailable"}, status=status.HTTP_400_BAD_REQUEST)

        if not self._can_access_lesson(student, lesson):
            return Response({"error": "يجب عليك اجتياز جميع الامتحانات المطلوبة للدخول إلى هذا الدرس"}, status=status.HTTP_403_FORBIDDEN)

        get_views, _ = LessonView.objects.get_or_create(student=student, lesson=lesson)
        if get_views.counter >= lesson.view:
            return Response({"error": "You don't have views for this lesson"}, status=status.HTTP_400_BAD_REQUEST)

        return self._get_lesson_response(student, course, lesson)
    
    def _can_access_lesson(self, student, lesson):
        """
        Check if a student can access a lesson based on required exams.
        A student must pass all required exams before proceeding.
        """

        # Get all exams that are dependencies and come before this lesson
        dependent_exams = Exam.objects.filter(
            unit=lesson.unit, 
            order__lt=lesson.order, 
            is_depends=True
        )

        for exam in dependent_exams:
            # Check if the student has a result for this exam
            result = Result.objects.filter(student=student, exam=exam).first()
            
            # If no result or not passed, restrict access
            if not result or not result.is_succeeded:
                return False  # The student hasn't passed a required exam

        return True  # The student has passed all required exams

    def _get_lesson_response(self, student, course, lesson):
        
        if lesson.video_url:
            payload = {
                "student_id": student.id,
                "course_id": course.id,
                "lesson_id": lesson.id,
                "video_id": lesson.id,
                "lesson_name": lesson.name,
                "unit_name": lesson.unit.name,
                "video_url": lesson.video_url,
                "token": student.jwt_token,
                "base_url": settings.BASE_URL,
                "platform_name": settings.PLATFORM_NAME,
                "request_delay": settings.REQUEST_DELAY,
            }
            return Response({"en_data": encrypt_data(payload), **AccessLessonSerializer(lesson).data}, status=status.HTTP_200_OK)

        if lesson.vdocipher_id:
            response = requests.post(
                f"https://dev.vdocipher.com/api/videos/{lesson.vdocipher_id}/otp",
                json={"ttl": 300},
                headers={
                    "Authorization": f"Apisecret {settings.VDO_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            return Response({**AccessLessonSerializer(lesson).data, "credentials": response.json()}, status=status.HTTP_200_OK)
        
        if lesson.youtube_url:
            return Response({**AccessLessonSerializer(lesson).data,"youtube_url": lesson.youtube_url}, status=status.HTTP_200_OK)



        return Response({"error": "Lesson is not accessible"}, status=status.HTTP_400_BAD_REQUEST)

    def _access_file(self, course, file_id, student):
        file = get_object_or_404(File, id=file_id)
        if file.unit.course != course:
            return Response({"error": "This file does not belong to the specified course"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AccessFileSerializer(file).data, status=status.HTTP_200_OK)


class AccessLessonByCode(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request ,lesson_id, *args, **kwargs):

        lesson = get_object_or_404(Lesson,id=lesson_id)
        student = request.user.student
        
        if not LessonSubscription.objects.filter(
            student=student, lesson=lesson, active=True).exists():
            Response(
                {"error": "You do not have access permissions"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        if lesson.video_url:
            payload = {
                "student_id": student.id,
                "course_id": lesson.unit.course.id,
                "lesson_id": lesson.id,
                "video_id": lesson.id,
                "lesson_name": lesson.name,
                "unit_name": lesson.unit.name,
                "video_url": lesson.video_url,
                "token": student.jwt_token,
                "base_url": settings.BASE_URL,
                "platform_name": settings.PLATFORM_NAME,
                "request_delay": settings.REQUEST_DELAY,
            }
            encrypted_data = encrypt_data(payload)
            serializer = AccessLessonSerializer(lesson)
            context = {
                "en_data": encrypted_data,
                **serializer.data,
            }
            return Response(context, status=status.HTTP_200_OK)
        
        # If the lesson is not ready but has a VdoCipher ID, get credentials
        elif lesson.vdocipher_id:
            url = f"https://dev.vdocipher.com/api/videos/{lesson.vdocipher_id}/otp"
            payloadStr = json.dumps({'ttl': 300})
            headers = {
                'Authorization': f"Apisecret {settings.VDO_API_KEY}",
                'Content-Type': "application/json",
                'Accept': "application/json"
            }

            response = requests.post(url, data=payloadStr, headers=headers)
            serializer = AccessLessonSerializer(lesson)
            context = {
                **serializer.data,
                "credentials": json.loads(response.text)
            }
            return Response(context, status=status.HTTP_200_OK)
        
        elif lesson.youtube_url:
            serializer = AccessLessonSerializer(lesson)
            context = {
                **serializer.data,
            }
            return Response(context, status=status.HTTP_200_OK)

        return Response("no lesson in this code",status=status.HTTP_200_OK)



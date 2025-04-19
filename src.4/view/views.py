# Django lib
from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from datetime import timedelta
# RestFrameWork lib
from rest_framework import status
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
# Apps Models
from student.models import Student
from course.models import *
from subscription.models import CourseSubscription
from analysis.models import StudentPoint
from .models import *
import uuid
# Create your views here.

class ViewsProgress(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lesson = get_object_or_404(Lesson, id=request.data.get("lesson_id"))
        student = request.user.student
        duration_second = int(request.data.get("duration_second"))
        time_second = int(request.data.get("time_second"))
        manasa_percentage = int(settings.WATCHED_PERCENTAGE)
        watched_percentage = (time_second / duration_second) * 100
        session_id = request.data.get("session_id", None)
        
        # Get or Create LessonView
        lesson_view, lesson_view_created = LessonView.objects.get_or_create(
            lesson=lesson,
            student=student
        )


        # Update LessonView
        if watched_percentage >= manasa_percentage and lesson_view.status == 0:
            
            # Increase counter
            lesson_view.counter += 1
            lesson_view.status = 1

            # Increase video views
            get_lesson = lesson_view.lesson
            get_lesson.video_views += 1
            
            # Save
            get_lesson.save()
            lesson_view.save()





        # Update LessonView
        elif watched_percentage <= manasa_percentage:
            lesson_view.status = 0
            lesson_view.save()

        
        # Update total watch time
        if lesson_view.total_watch_time < duration_second:
            lesson_view.total_watch_time = time_second
            lesson_view.save()



        if session_id:
            # Get or Create ViewSession
            session,session_created = ViewSession.objects.get_or_create(
                session=session_id,
                view=lesson_view
            )

            session.watch_time = time_second
            session.save()


        return Response(request.data, status=status.HTTP_200_OK)

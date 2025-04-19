# Django lib
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum, Q

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
from rest_framework.parsers import MultiPartParser, FormParser
#Python lib
from datetime import timedelta
#App Models
from exam.models import Exam, Result
from student.models import *
from course.models import Lesson
from subscription.models import CourseSubscription
from view.models import LessonView
from course.models import Lesson

class ProfileAnalysis(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Retrieve the student from the authenticated user
        student = request.user.student

        progress_data = self._get_student_progress_in_all_courses(student)
        exam_data = self._get_student_exam_progress(student)
        watch_time_data = self._get_student_total_watch(student)
        context = {
            "progress_in_all_courses": progress_data,
            "exam_progress": exam_data,
            "total_watch_time":watch_time_data,
        }
        return Response(context, status=status.HTTP_200_OK)

    def _get_student_progress_in_all_courses(self, student):
        # Query to get all subscribed courses for the student
        subscribed_courses = CourseSubscription.objects.filter(student=student).select_related('course')

        # Initialize counters for watched and total lessons
        total_lessons = 0
        watched_lessons = 0

        for subscription in subscribed_courses:
            course = subscription.course
            total_lessons += Lesson.objects.filter(unit__course=course, pending=False).count()
            watched_lessons += LessonView.objects.filter(
                lesson__unit__course=course,
                student=student,
                counter__gt=0
            ).count()

        # Return the aggregated progress as a dictionary
        return {
            "watched_lessons": watched_lessons,
            "total_lessons": total_lessons
        }

    def _get_student_exam_progress(self, student):
        # Get all exams related to the student
        exams = Exam.objects.filter(results__student=student).distinct()
        # Get all subscribed courses for the student
        subscribed_courses = CourseSubscription.objects.filter(student=student).select_related('course')
        # Initialize counters
        total_exams_taken = 0
        total_exam_scores = 0
        total_student_scores = 0

        # Calculate the total number of exams that should be taken
        total_exams_should_be_taken = Exam.objects.filter(
            Q(start__lte=timezone.now(), end__gte=timezone.now()) | Q(end__lt=timezone.now()),
            unit__course__in=[subscription.course for subscription in subscribed_courses]
        ).count() + Exam.objects.filter(
            Q(start__lte=timezone.now(), end__gte=timezone.now()) | Q(end__lt=timezone.now()),
            lesson__unit__course__in=[subscription.course for subscription in subscribed_courses]
        ).count()

        for exam in exams:
            result = Result.objects.filter(student=student, exam=exam).first()
            if result:
                active_trial = result.active_trial  # Fetch the active trial
                if active_trial:
                    total_exams_taken += 1
                    total_exam_scores += active_trial.exam_score  # Use exam_score from active_trial
                    total_student_scores += active_trial.score  # Use score from active_trial

        # Return the aggregated exam progress as a dictionary
        return {
            "total_exams_should_be_taken": total_exams_should_be_taken,
            "total_exams_taken": total_exams_taken,
            "total_exam_scores": total_exam_scores,
            "total_student_scores": total_student_scores,
        }

    def _get_student_total_watch(self,student):
        total_time = 0
        for i in LessonView.objects.filter(student=student,counter__gte=1):
            total_time+= i.total_watch_time
        
        hours =  total_time / 3600 
        
        return round(hours,1)


class UserActivityAnalysis(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # 1. Get user activity table data
        activities = UserActivity.objects.filter(user=user).values(
            'device_name',
            'os_name',
            'browser_name',
            'last_active',
            'login_time',
            'logout_time'
        )
        
        # 2. Get total login/logout counts
        total_logins = activities.count()
        total_logouts = activities.exclude(logout_time=None).count()
        
        # 3. Get logout count for last 7 days
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_logouts = activities.filter(
            logout_time__gte=seven_days_ago
        ).count()
        
        return Response({
            'activity_table': activities,
            'total_logins': total_logins,
            'total_logouts': total_logouts,
            'logouts_last_7_days': recent_logouts
        })


class TopStudent(APIView):
    def get(self, request):
        
        return Response(status=status.HTTP_200_OK)
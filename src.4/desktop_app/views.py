from django.conf import settings
from rest_framework import status
from django.db.models import OuterRef, Subquery, IntegerField, Value, F,Q
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from student.models import Student
from course.models import *
from view.models import *
from exam.models import ResultTrial
from subscription.models import CourseSubscription
from dashboard.pagination import CustomPageNumberPagination
from invoice.models import Invoice
from django.utils import timezone
from django.shortcuts import get_object_or_404 
from .serializers import *
from .permissions import HasValidAPIKey
from .models import *
from datetime import datetime 
# Create your views here.

# Student
class StudentList(generics.ListAPIView):
    queryset = Student.objects.select_related('user', 'type_education', 'year').filter(by_code=True).order_by("-created")
    serializer_class = StudentListSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

# Course
class CourseList(generics.ListAPIView):
    queryset = Course.objects.filter(center=True)
    serializer_class = CourseListSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

# Lesson
class LessonList(generics.ListAPIView):
    queryset = Lesson.objects.filter(unit__course__center=True)
    serializer_class = LessonListSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

# Lesson Views
class LessonViewsList(APIView):
    serializer_class = LessonViewSerializer
    permission_classes = [HasValidAPIKey]
    lookup_field = 'lesson_id'
    throttle_classes = []
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        course = lesson.unit.course

        # Get all students subscribed to the course
        subscriptions = CourseSubscription.objects.filter(course=course, active=True)
        students = [sub.student for sub in subscriptions]

        # Get LessonViews for the lesson
        lesson_views = LessonView.objects.filter(lesson=lesson, student__in=students)

        # Map existing views by student ID for quick lookup
        views_by_student_id = {lv.student_id: lv for lv in lesson_views}

        # Build final list (real or manual data for students without views)
        full_data = []
        for student in students:
            if student.id in views_by_student_id:
                full_data.append(views_by_student_id[student.id])
            else:
                # Manually create a dictionary for a non-viewed student
                full_data.append({
                    'lesson': lesson,
                    'student': student,
                    'total_watch_time': 0,
                    'status': 0,
                    'counter': 0,
                })

        # Paginate the data
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(full_data, request)
        
        # Serialize the paginated data
        serializer = self.serializer_class(result_page, many=True)

        # Return the paginated response
        return paginator.get_paginated_response(serializer.data)
    
# Exam
class ExamList(generics.ListAPIView):
    permission_classes = [HasValidAPIKey]
    serializer_class = ExamSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

    def get_queryset(self):
        return Exam.objects.filter(Q(unit__course__center=True) | Q(lesson__unit__course__center=True))

class ExamResultList(generics.ListAPIView):
    permission_classes = [HasValidAPIKey]
    serializer_class = ExamResultSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

    def get_queryset(self):
        return Result.objects.filter(exam_id=self.kwargs.get('exam_id'),student__by_code=True)

class SubscribeManyUsers(APIView):
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

    def post(self, request):
        data = request.data
        student_codes = data.get('codes', [])
        course = get_object_or_404(Course, id=data.get('course_id'))
        
        students = Student.objects.filter(code__in=student_codes)
        existing_subscriptions = CourseSubscription.objects.filter(
            student__in=students, course=course, active=True
        ).values_list('student_id', flat=True)

        new_subscriptions = [
            CourseSubscription(student=student, course=course, active=True)
            for student in students if student.id not in existing_subscriptions
        ]

        if new_subscriptions:
            try:
                CourseSubscription.objects.bulk_create(new_subscriptions, ignore_conflicts=True)
            except :
                return Response({'message': 'Error creating subscriptions'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Success'}, status=status.HTTP_200_OK)

class UnSubscribeManyUsers(APIView):
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

    def post(self, request):
        codes = request.data.get('codes', [])
        course_id = request.data.get('course_id')
        
        course = get_object_or_404(Course, id=course_id)
        students = Student.objects.filter(code__in=codes)
        
        subscriptions = CourseSubscription.objects.filter(student__in=students, course=course)
        updated_count = subscriptions.delete()
        
        return Response({'message': 'Success', 'deleted_count': updated_count}, status=status.HTTP_200_OK)

class SubmitResultExam(APIView):
    def post(self, request, *args, **kwargs):  
        exam_name = request.data.get("exam_name")
        lecture_name = request.data.get("lecture_name")
        exam_date_raw = request.data.get("exam_date")

        # Convert date string to date object
        try:
            exam_date = datetime.fromisoformat(str(exam_date_raw)).date() if exam_date_raw else None
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        for result in request.data.get("results", []):
            user_code = result.get('user_code')
            try:
                student = Student.objects.get(code=user_code)
            except Student.DoesNotExist:
                continue  # Skip if student not found

            obj, created = ResultExamCenter.objects.get_or_create(
                name=exam_name,
                lecture=lecture_name,
                student=student,
            )
            obj.date = exam_date
            obj.result_percentage = result.get('result_percentage')
            obj.result_photo = result.get('file_url')
            obj.save()

        return Response({"message": "Results processed."}, status=status.HTTP_200_OK)

#* =================================Center================================= *#

class CenterList(generics.ListAPIView):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

class CenterCreate(generics.CreateAPIView):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

#* =================================Lecture================================= *#

class LectureList(generics.ListAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []

class LectureCreate(generics.CreateAPIView):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [HasValidAPIKey]
    throttle_classes = []

#* =================================Attendance================================= *#

class AttendanceList(generics.ListAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [HasValidAPIKey]
    filter_backends = [DjangoFilterBackend,SearchFilter]
    pagination_class = CustomPageNumberPagination
    throttle_classes = []


class AttendanceCreate(APIView):
    permission_classes = [HasValidAPIKey]
    queryset = Attendance.objects.all()

    def post(self, request, *args, **kwargs):
        data = request.data
        lecture_name = data.get('lecture_name')
        attendance_status = data.get('status')
        date = data.get("date")
        students_codes = data.get('students_codes')

        lecture = get_object_or_404(Lecture, name=lecture_name)
        students_in = []
        skipped_students = []

        for code in students_codes:
            student = Student.objects.filter(code=code).first()  # Check if student exists

            if not student:
                skipped_students.append(code)  # Track skipped students
                continue  # Skip to the next iteration

            attendance, _ = Attendance.objects.update_or_create(
                student=student,
                lecture=lecture,
                date=date,
                defaults={'status': attendance_status}  # Use defaults for update_or_create
            )

            students_in.append(code)

        return Response(
            {
                "message": "Attendance processed successfully.",
                "students_marked": students_in,
                "students_skipped": skipped_students
            },
            status=status.HTTP_201_CREATED
        )
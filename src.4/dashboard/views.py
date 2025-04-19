# Django lib
import ast
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db.models import F, BooleanField, Sum, Case, When, Value,Q,Count,FloatField,Subquery, OuterRef, Q
from django.db.models.functions import Cast, Coalesce,TruncDate
from django.db.models import QuerySet
from rest_framework.parsers import JSONParser
from django.db import transaction
from typing import List, Dict, Any
from datetime import datetime, timedelta
from django.contrib.auth.models import Permission
from django.db.models import Prefetch
from django.utils.dateparse import parse_datetime
# RestFrameWork lib
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, filters, status
from rest_framework.filters import SearchFilter,OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import CustomDjangoModelPermissions
from .pagination import CustomPageNumberPagination
# Apps Models
from exam.models import Exam,DifficultyLevel, ExamQuestion, ExamType, QuestionType, RandomExamBank, RelatedToChoices, Result, Submission,ExamModel, ExamModelQuestion
from student.models import Student,StudentCode
from course.models import Course,CourseCode,LessonFile,AnyLessonCode
from invoice.models import Invoice,PromoCode
from subscription.models import CourseSubscription,LessonSubscription
from view.models import *
from analysis.models import StudentPoint
# Serializers
from .serializers.student.student import *
from .serializers.course.course import *
from .serializers.course.unit import *
from .serializers.course.lesson import *
from .serializers.course.file import *
from .serializers.invoice.invoice import *
from .serializers.invoice.promo_code import *
from .serializers.subscription.subscriptions import *
from .serializers.exam.exam import *
from .serializers.view.lesson_view import *
from .serializers.extra.news import *
from .serializers.extra.update import *
from .serializers.codes.course_code import *
from .serializers.codes.lesson_code import *
from .serializers.analysis.analysis import *
from .serializers.permissions.permissions import *
from .serializers.course_collections.course_collections import *
from .serializers.requestlogs.requestlogs import RequestLogSerializer
from .serializers.codes.student_code import StudentCodeSerializer
from .filters import *


# views 

# ap:Student
#^ < ==============================[ <- Student -> ]============================== > ^#

class StudentsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset = Student.objects.select_related('user', 'type_education', 'year').order_by("-created")
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = [
            'year',
            'by_code',
            'type_education',
            'government',
            'user__is_staff',
            ]

    search_fields = [
        'name',
        'code',
        'user__username',
        ]


class StudentUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    serializer_class = UpdateStudentSerializer
    lookup_field = 'id'


class StudentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'id'


class UserDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = User.objects.all()
    lookup_field = 'username'


class UserRestPasswordView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()

    def post(self , request , username , *args, **kwargs):
        new_password = request.data.get("new_password")
        user = get_object_or_404(User,username=username)

        user.set_password(new_password)
        user.save()

        return Response(status=status.HTTP_200_OK)


class ChangeStudentByCode(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    def post(self,request,*args, **kwargs):
        student_id = request.data.get("student_id")
        active_code = request.data.get("active_code")
        student = get_object_or_404(Student,id=student_id)
        student.by_code = False
        student.save()
        if active_code:
            get_code = get_object_or_404(StudentCode,code=student.code)
            get_code.student = None
            get_code.available = True
            get_code.save()
            student.code = None
            student.save()
        return Response(status=status.HTTP_200_OK)


class StudentSignCodeView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    
    def post(self,request,*args, **kwargs):
        code = request.data.get("code")
        student_id = request.data.get("student_id")
        student = get_object_or_404(Student,id=student_id)

        # is student edit the code before  
        if student.by_code:
            return Response({"error":"you are can not add your code "},status=status.HTTP_406_NOT_ACCEPTABLE)
        
        try:
            code = StudentCode.objects.get(code=code)
            
            # if the code is already taken 
            if code.available == False:
                return Response({"error":"this code is already taken"},status=status.HTTP_406_NOT_ACCEPTABLE)
            
            # else sign code to student and make student by_code = True
            # update code
            code.available = False
            code.student=student
            # update student
            student.by_code = True
            student.code = code.code
            # saves
            code.save()
            student.save()
        
        except StudentCode.DoesNotExist:
            return Response({"error":"This Code Does Not Exist"},status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_201_CREATED)


#ap:Admins
#^ < ==============================[ <- Admins -> ]============================== > ^#

class CreateAdminView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        name = request.data.get("name")

        if not username or not password or not email:
            return Response(
                {"error": "Username, password, and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=True
        )
        student = Student.objects.create(
            user= user,
            name = name,
            parent_phone = "admin",
            type_education_id = 1,
            year_id = 3,
            government = "admin",
            jwt_token = "admin",
            active = 1,
            is_admin = 1,
        )

        return Response(
            {"message": "User created successfully", "username": user.username},
            status=status.HTTP_201_CREATED,
        )

class AdminListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    queryset = User.objects.filter(is_staff=True)
    serializer_class = UserWithPermissionSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = ['username']


#ap:Analysis
#^ < ==============================[ <- Analysis -> ]============================== > ^#

class StudentPointListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentPoint.objects.all().order_by("-created")
    serializer_class = StudentPointSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = ['student','point_type']
    search_fields = ['student__name','student__user__username','points_note']


class AllLessonListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Lesson.objects.all().order_by("-created")
    serializer_class = ListLessonVideoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['unit', 'pending','unit__course']  
    search_fields = ['name', 'description', 'unit__course__name']


class ChartDataInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Invoice.objects.all()
    def get(self, request, *args, **kwargs):
        today = timezone.now()
        start_date = request.query_params.get('start_date', today - timedelta(days=14))
        end_date = request.query_params.get('end_date', today)

        invoices = (
            Invoice.objects.filter(created__date__gte=start_date, created__date__lte=end_date)
            .values('created__date')
            .annotate(
                unpaid=Count('id', filter=Q(pay_status='P')),
                paid=Count('id', filter=Q(pay_status='C')),
                failed=Count('id', filter=Q(pay_status='F')),
                expired=Count('id', filter=Q(pay_status='E')),
            )
            .order_by('created__date')
        )

        data = {
            "dates": [i['created__date'].strftime('%Y-%m-%d') for i in invoices],
            "unpaid": [i['unpaid'] for i in invoices],
            "paid": [i['paid'] for i in invoices],
            "failed": [i['failed'] for i in invoices],
            "expired": [i['expired'] for i in invoices],
        }
        return Response(data)


class StudentsPerGovernmentView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Student.objects.all()

    def get(self, request):
        active_student = request.query_params.get('active_student') == 'false'

        data = (
            Student.objects.filter(active=True).values("government").annotate(count=Count("id")).order_by("-count")
            if active_student else
            Student.objects.filter(coursesubscription__active=True)
            .values("government").distinct()
            .annotate(count=Count("id")).order_by("-count")
        )

        return Response(data)


class StudentsOverTimeView(APIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset = Student.objects.all()
    def get(self, request):
        data = (
            Student.objects.annotate(date=TruncDate("created"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return Response(data)


class CourseProgressView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = LessonView.objects.all()
    
    def get(self, request, course_id):
        lessons = Lesson.objects.filter(unit__course_id=course_id).order_by('order')
        lesson_ids = list(lessons.values_list('id', flat=True))

        students = Student.objects.filter(
            coursesubscription__course=course_id,
            coursesubscription__active=True
        ).distinct()

        # Paginate students directly
        paginator = CustomPageNumberPagination()
        paginator.page_size = 100
        paginated_students = paginator.paginate_queryset(students, request)

        # Fetch all relevant lesson views once
        lesson_views = LessonView.objects.filter(
            lesson_id__in=lesson_ids,
            student_id__in=[s.id for s in paginated_students]
        )

        # Index lesson_views by (student_id, lesson_id)
        from collections import defaultdict
        lesson_views_dict = defaultdict(dict)
        for view in lesson_views:
            lesson_views_dict[view.student_id][view.lesson_id] = view

        result = []
        for student in paginated_students:
            student_progress = {
                "student_id": student.id,
                "student_name": student.name,
                "student_username": student.user.username,
                "student_parent_phone": student.parent_phone,
                "student_code": student.code,
                "lessons": {}
            }

            for lesson in lessons:
                view = lesson_views_dict.get(student.id, {}).get(lesson.id)

                if view and lesson.video_duration:
                    progress = (view.total_watch_time / (lesson.video_duration * 60)) * 100
                    progress = round(min(progress, 100), 2)
                else:
                    progress = 0

                student_progress["lessons"][lesson.name] = progress

            result.append(student_progress)

        return paginator.get_paginated_response(result)


#ap:Course
#^ < ==============================[ <- CourseCategory -> ]============================== > ^#

class CourseCategoryListView(generics.ListAPIView):
    queryset = CourseCategory.objects.all().order_by("-created")
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']

class CourseCategoryCreateView(generics.CreateAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

class CourseCategoryUpdateView(generics.UpdateAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    lookup_field = 'id'

class CourseCategoryDeleteView(generics.DestroyAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    lookup_field = 'id'

#^ < ==============================[ <- Course Collection -> ]============================== > ^#

class CourseCollectionListView(generics.ListAPIView):
    queryset = CourseCollection.objects.all().order_by("-created")
    serializer_class = CourseCollectionListSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]


class CourseCollectionCreateView(generics.CreateAPIView):
    queryset = CourseCollection.objects.all()
    serializer_class = CourseCollectionCreateUpdateSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]


class CourseCollectionUpdateView(generics.RetrieveUpdateAPIView):
    queryset = CourseCollection.objects.all()
    serializer_class = CourseCollectionCreateUpdateSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]


class CourseCollectionDeleteView(generics.DestroyAPIView):
    queryset = CourseCollection.objects.all()
    serializer_class = CourseCollectionListSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]


#^ < ==============================[ <- Course -> ]============================== > ^#

class CourseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset = Course.objects.all().order_by("-created")
    serializer_class = ListCourseSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = ['year','pending','center','category']

    search_fields = ['name','description',]


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all() 
    serializer_class = ListCourseSerializer
    lookup_field = 'id'


class CourseCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateCourseSerializers
    queryset = Course.objects.all()


class CourseUpdateView(generics.UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = UpdateCourseSerializer
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]  
    lookup_field = 'id'


class CourseDeleteView(generics.DestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = ListCourseSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    lookup_field = 'id'

#^ < ==============================[ <- Unit -> ]============================== > ^#

class UnitListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListUnitSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['pending']
    search_fields = ['name', 'description']

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Unit.objects.filter(course_id=course_id).order_by("order")


class UnitContentView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Unit.objects.all()

    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Unit, id=unit_id)
        content = self.get_content(unit)
        return Response(content, status=status.HTTP_200_OK)

    def get_content(self, unit):
        lessons = self.get_lessons(unit)
        files = self.get_files(unit)
        exams = self.get_exams(unit)

        # Combine and sort lessons, files, and exams by 'order'
        combined_content = self.combine_content(lessons, files, exams)
        return combined_content

    def get_lessons(self, unit):
        # Retrieve and serialize lessons associated with the unit
        lessons = unit.unit_lessons.all()
        return ListLessonSerializer(lessons, many=True).data

    def get_files(self, unit):
        # Retrieve and serialize files associated with the unit
        files = unit.files.all()
        return ListFileSerializer(files, many=True).data

    def get_exams(self, unit):

        # Exams related to  unit
        unit_exams = Exam.objects.filter(unit=unit)

        return ExamSerializer(unit_exams, many=True).data

    def combine_content(self, lessons, files, exams):
        # Combine lessons, files, and exams into a unified list, sorted by 'order'
        combined_content = sorted(
            [{'content_type': 'lesson', **lesson} for lesson in lessons] +
            [{'content_type': 'file', **file} for file in files] +
            [{'content_type': 'exam', **exam} for exam in exams],
            key=lambda x: x.get('order', 0)  # Assuming 'order' is available; default to 0 if not
        )
        return combined_content


class UnitCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateUnitSerializer
    queryset = Unit.objects.all()

    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        serializer.save(course=course)


class UnitUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = UpdateUnitSerializer
    queryset = Unit.objects.all()
    def get_object(self):
        unit_id = self.kwargs.get('unit_id')
        return get_object_or_404(Unit, id=unit_id)


class UnitDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListUnitSerializer
    queryset = Unit.objects.all()
    
    def get_object(self):
        unit_id = self.kwargs.get('unit_id')
        return get_object_or_404(Unit, id=unit_id)

#^ < ==============================[ <- Lesson -> ]============================== > ^#

class LessonListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListLessonSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['pending']
    search_fields = ['name', 'description']
    queryset = Lesson.objects.all()

    def get_queryset(self):
        unit_id = self.kwargs.get('unit_id')
        if not unit_id:
            return Lesson.objects.none()
        return Lesson.objects.filter(unit=unit_id)


class LessonCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateLessonSerializer
    queryset = Lesson.objects.all() 

    def perform_create(self, serializer):
        unit_id = self.kwargs.get('unit_id')
        unit = get_object_or_404(Unit, id=unit_id)
        serializer.save(unit=unit)


class LessonUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = UpdateLessonSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def get_object(self):
        lesson_id = self.kwargs.get('lesson_id')
        return get_object_or_404(Lesson, id=lesson_id)



class LessonDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListLessonSerializer
    queryset = Lesson.objects.all()

    def get_object(self):
        lesson_id = self.kwargs.get('lesson_id')
        return get_object_or_404(Lesson, id=lesson_id)

#^ < ==============================[ <- Lesson File -> ]============================== > ^#

class LessonFileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileLessonSerializer 
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        return LessonFile.objects.filter(lesson=lesson_id)

class LessonFileCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileLessonSerializer
    queryset = LessonFile.objects.all()

    def perform_create(self, serializer):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        serializer.save(lesson=lesson)


class LessonFileUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileLessonSerializer
    queryset = LessonFile.objects.all()

    def get_object(self):
        file_id = self.kwargs.get('file_id')
        return get_object_or_404(LessonFile, id=file_id)


class LessonFileDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = FileLessonSerializer
    queryset = LessonFile.objects.all()

    def get_object(self):
        file_id = self.kwargs.get('file_id')
        return get_object_or_404(LessonFile, id=file_id)



#^ < ==============================[ <- File -> ]============================== > ^#

class FileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListFileSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['pending']
    search_fields = ['name']
    
    def get_queryset(self):
        unit_id = self.kwargs['unit_id']
        return File.objects.filter(unit=unit_id)


class FileCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = CreateFileSerializer
    queryset = File.objects.all()

    def perform_create(self, serializer):
        unit_id = self.kwargs.get('unit_id')
        unit = get_object_or_404(Unit, id=unit_id)
        serializer.save(unit=unit)


class FileUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = UpdateFileSerializer
    queryset = File.objects.all()

    def get_object(self):
        file_id = self.kwargs.get('file_id')
        return get_object_or_404(File, id=file_id)


class FileDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListFileSerializer
    queryset = File.objects.all()

    def get_object(self):
        file_id = self.kwargs.get('file_id')
        return get_object_or_404(File, id=file_id)

#^ < ==============================[ <- Content -> ]============================== > ^#

class ContentDetails(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Unit.objects.all()

    def get(self, request, course_id, content_type, content_id, *args, **kwargs):
        # Fetch course and student
        course = get_object_or_404(Course, id=course_id)
        student = request.user.student

        # Handle content access
        if content_type == "lesson":
            return self._lesson_details(course, content_id)
        elif content_type == "file":
            return self._file_details(course, content_id)
        else:
            return Response(
                {"error": "Invalid content type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _lesson_details(self, course, lesson_id):

        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Validate lesson belongs to the course
        if lesson.unit.course != course:
            return Response(
                {"error": "This lesson does not belong to the specified course"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return serialized lesson data
        return Response(ListLessonSerializer(lesson).data, status=status.HTTP_200_OK)

    def _file_details(self, course, file_id):
        """
        Handle file access logic.
        """
        file = get_object_or_404(File, id=file_id)

        # Validate file belongs to the course
        if file.unit.course != course:
            return Response(
                {"error": "This file does not belong to the specified course"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Return serialized file data
        return Response(ListFileSerializer(file).data, status=status.HTTP_200_OK)

#ap:Invoice
#^ < ==============================[ <- Invoice -> ]============================== > ^#


class InvoiceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ListInvoiceSerializer
    queryset = Invoice.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = InvoiceFilter
    search_fields = ['student__user__username', 'sequence', 'promo_code__code', 'fawry_reference_number']


class UpdateInvoicePayStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Invoice.objects.all()
    serializer_class = UpdateInvoiceSerializer
    lookup_field = 'id'  


class CreateInvoiceManually(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Invoice.objects.all()

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        course_id = request.data.get("course_id")
        paid = request.data.get("paid", None)

        # Fetch the student and course or return 404 if not found
        get_student = get_object_or_404(Student, user__username=username)
        get_course = get_object_or_404(Course, id=course_id)

        
        # Check if an invoice with the same student and course already exists and is paid
        is_invoice_pay_exists = Invoice.objects.filter(student=get_student, course=get_course, pay_status='C').exists()
        if is_invoice_pay_exists:
            return Response({"invoice_pay_exists": is_invoice_pay_exists}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate price and set expiration time
        expires_at = timezone.now()
        price = paid if paid is not None else get_course.price

        # Create the invoice record
        create_invoice = Invoice.objects.create(
            student=get_student,
            course=get_course,
            price=price,
            pay_status='C',
            pay_method='M',
            expires_at=expires_at,
            pay_at=timezone.now(),
        )
        
        # Return the invoice sequence in the response
        return Response({"sequence": create_invoice.sequence}, status=status.HTTP_200_OK)

#ap:Subscription
#^ < ==============================[ <- Subscription -> ]============================== > ^#

class CourseSubscriptionList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all().order_by("-created")
    serializer_class = ListStudentCourseSubscription
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    search_fields = [
        'student__name',
        'student__user__username',
        'course__name',
        'invoice__sequence',
        ]

    filterset_fields = [
            'student',
            'course',
            'active',
            'student__government'
        ]

class CancelSubscription(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()

    def post(self,request,*args, **kwargs):
        subscription_id = request.data.get("subscription_id")
        get_subscription = get_object_or_404(CourseSubscription,id=subscription_id)
        get_subscription.active = False
        get_subscription.save()
        return Response(status=status.HTTP_200_OK) 

class CancelSubscriptionBulk(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()

    def post(self,request,*args, **kwargs):
        student_id = request.data.get("student_id")
        get_subscriptions = CourseSubscription.objects.filter(student_id=student_id)
        get_subscriptions.update(active=False)
        return Response(status=status.HTTP_200_OK)

class SubscriptionManyStudent(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseSubscription.objects.all()
    
    def post(self, request, *args, **kwargs):
        students_list = request.data.get("students", [])
        course_id = request.data.get("course_id")

        skipped_students = []

        for student in students_list:
            try:
                get_student = Student.objects.get(Q(user__username=student) | Q(code=student))
                CourseSubscription.objects.get_or_create(
                    student=get_student,
                    course_id=course_id,
                    active=True
                )
            except Student.DoesNotExist:
                skipped_students.append(student)

        return Response({"skipped_students": skipped_students}, status=status.HTTP_200_OK)
    
#ap:View
#^ < ==============================[ <- View -> ]============================== > ^#

class LessonViewList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = LessonView.objects.filter(counter__gte = 1).order_by("-created")
    serializer_class = ListLessonViewListSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    search_fields = [
        'student__user__username',
        'student__name',
    ]
    filterset_fields = [
        'lesson',
        'lesson__unit__course',
    ]

class UpdateStudentView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = LessonView.objects.all()

    def post(self,request,view_id,*args, **kwargs):

        counter_amount = request.data.get("counter_amount")

        view = get_object_or_404(LessonView,id=view_id)
        view.counter -= int(counter_amount)
        view.save()

        return Response(status=status.HTTP_200_OK)

class StudentsNotViewedLesson(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = LessonView.objects.all()

    def get(self, request, lesson_id, *args, **kwargs):
        # Get the lesson or return a 404 error if not found
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Get IDs of students subscribed to the course and active
        subscribed_students = CourseSubscription.objects.filter(
            course=lesson.unit.course, active=True
        ).values_list('student_id', flat=True)

        # Filter students who have not viewed the lesson (counter < 1 or no entry in LessonView)
        not_viewed_students = Student.objects.filter(id__in=subscribed_students).exclude(
            id__in=LessonView.objects.filter(
                lesson=lesson, counter__gte=1
            ).values_list('student_id', flat=True)
        )

        # Paginate the data
        paginator = CustomPageNumberPagination()
        paginated_students = paginator.paginate_queryset(not_viewed_students, request)

        # Serialize the data
        serializer = StudentSerializer(paginated_students, many=True)

        return paginator.get_paginated_response(serializer.data)


#ap:Exam
#^ < ==============================[ <- Exam -> ]============================== > ^#
#^ Exam
#^ Dashboard Part (admin responsibility)
class ExamListCreateView(generics.ListCreateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['related_to', 'is_active', 'unit', 'lesson', 'type']
    ordering_fields = ['start', 'end']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status (existing logic)
        status = self.request.query_params.get("status")
        if status:
            now = timezone.now()
            if status == "soon":
                queryset = queryset.filter(start__gt=now)
            elif status == "active":
                queryset = queryset.filter(start__lte=now, end__gte=now)
            elif status == "finished":
                queryset = queryset.filter(end__lt=now)

        # Filter by related_course
        related_course = self.request.query_params.get("related_course")
        if related_course:
            queryset = queryset.filter(
                models.Q(unit__course_id=related_course) | models.Q(lesson__unit__course_id=related_course)
            )

        # Filter by related_year
        related_year = self.request.query_params.get("related_year")
        if related_year:
            queryset = queryset.filter(
                models.Q(unit__course__year_id=related_year) | models.Q(lesson__unit__course__year_id=related_year)
            )

        return queryset

    def perform_create(self, serializer):
        """
        Validate and save the exam, ensuring model-level validation is triggered.
        """
        if serializer.is_valid():
            try:
                exam = serializer.save()
                exam.clean()  # Trigger model validation
            except ValidationError as e:
                return Response({"errors": e.messages}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExamDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

#^ QuestionCategory 
class QuestionCategoryListCreateView(generics.ListCreateAPIView):
    queryset = QuestionCategory.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = QuestionCategorySerializer
    filterset_fields = ['year']


class QuestionCategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = QuestionCategory.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = QuestionCategorySerializer

#^ Question , Answer
class QuestionListCreateView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = QuestionSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = {
        'lesson': ['exact'],
        'is_active': ['exact'],
        'category__year': ['exact'],
        'difficulty': ['exact'],
        'category': ['exact'],
        'unit__course': ['exact'],
        'question_type': ['exact'],
    }
    search_fields = ['text', 'answers__text']

    def create(self, request, *args, **kwargs):
        try:
            # Extract basic question data
            question_data = {
                'text': request.data.get('text'),
                'points': request.data.get('points'),
                'difficulty': request.data.get('difficulty'),
                'category': request.data.get('category'),
                'lesson': request.data.get('lesson'),
                'unit': request.data.get('unit'),
                # 'is_active': request.data.get('is_active') == 'true',
                'question_type': request.data.get('question_type'),
            }

            # Handle question image
            if 'image' in request.FILES:
                question_data['image'] = request.FILES.get('image')

            # Create question
            question_serializer = self.get_serializer(data=question_data)
            question_serializer.is_valid(raise_exception=True)
            question = question_serializer.save()

            # Process answers
            index = 0
            while f'answers[{index}][text]' in request.data:
                answer_data = {
                    'question': question.id,
                    'text': request.data[f'answers[{index}][text]'],
                    'is_correct': request.data.get(f'answers[{index}][is_correct]', '').lower() == 'true',
                }
                
                # Handle answer image
                image_key = f'answers[{index}][image]'
                if image_key in request.FILES:
                    answer_data['image'] = request.FILES[image_key]
                
                answer_serializer = AnswerSerializer(data=answer_data)
                if answer_serializer.is_valid():
                    answer_serializer.save()
                else:
                    # If answer creation fails, delete the question and return error
                    question.delete()
                    return Response(
                        answer_serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                index += 1

            # Return the created question with its answers
            return Response(
                self.get_serializer(question).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class QuestionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            # Extract basic question data
            question_data = {}
            for field in ['text', 'points', 'difficulty', 'category', 'lesson', 'unit', 'question_type']:
                if field in request.data and request.data[field]:
                    question_data[field] = request.data[field]
            
            if 'is_active' in request.data:
                question_data['is_active'] = request.data['is_active'] == 'true'

            # Handle question image
            if 'image' in request.FILES:
                question_data['image'] = request.FILES.get('image')
            elif 'image' in request.data and not request.data['image']:
                pass

            # Update question
            question_serializer = self.get_serializer(instance, data=question_data, partial=True)
            question_serializer.is_valid(raise_exception=True)
            question = question_serializer.save()

            # Get existing answers
            existing_answers = {answer.id: answer for answer in question.answers.all()}

            # Process answers
            index = 0
            while f'answers[{index}][text]' in request.data:
                answer_text = request.data.get(f'answers[{index}][text]')
                answer_id = int(request.data.get(f'answers[{index}][id]'))
                
                if answer_id in existing_answers:
                    # Update existing answer
                    answer = existing_answers[answer_id]
                    answer_data = {
                        'text': answer_text,
                        'is_correct': request.data.get(f'answers[{index}][is_correct]', '').lower() == 'true',
                        'question': question.id
                    }

                    # Handle answer image if provided
                    image_key = f'answers[{index}][image]'
                    if image_key in request.FILES:
                        answer_data['image'] = request.FILES[image_key]

                    answer_serializer = AnswerSerializer(answer, data=answer_data, partial=True)
                    if answer_serializer.is_valid():
                        answer_serializer.save()
                    else:
                        return Response(
                            answer_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                index += 1

            return Response(self.get_serializer(question).data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BulkQuestionCreateView(generics.CreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    parser_classes = (MultiPartParser, FormParser)

    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def create(self, request, *args, **kwargs):
        try:
            created_questions = []
            exam = None
            
            # Check if exam_id is provided and valid
            exam_id = request.data.get('exam_id')
            if exam_id:
                try:
                    exam = Exam.objects.get(id=exam_id)
                except Exam.DoesNotExist:
                    return Response(
                        {'error': 'Exam not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            with transaction.atomic():  # Use transaction to ensure all or nothing
                # Determine how many questions we're creating
                question_count = 0
                while f'questions[{question_count}][text]' in request.data:
                    question_count += 1

                # Process each question
                for q_index in range(question_count):
                    # Extract question data
                    question_data = {
                        'text': request.data.get(f'questions[{q_index}][text]'),
                        'points': request.data.get(f'questions[{q_index}][points]'),
                        'difficulty': request.data.get(f'questions[{q_index}][difficulty]'),
                        'category': request.data.get(f'questions[{q_index}][category]'),
                        'lesson': request.data.get(f'questions[{q_index}][lesson]'),
                        'unit': request.data.get(f'questions[{q_index}][unit]'),
                        # 'is_active': request.data.get(f'questions[{q_index}][is_active]') == 'true',
                        'question_type': request.data.get(f'questions[{q_index}][question_type]'),
                    }

                    # Handle question image
                    image_key = f'questions[{q_index}][image]'
                    if image_key in request.FILES:
                        question_data['image'] = request.FILES[image_key]

                    # Create question
                    question_serializer = self.get_serializer(data=question_data)
                    question_serializer.is_valid(raise_exception=True)
                    question = question_serializer.save()

                    # If exam exists, link the question to it
                    if exam:
                        ExamQuestion.objects.create(
                            exam=exam,
                            question=question,
                            is_active=True
                        )

                    # Process answers for this question
                    answer_index = 0
                    while f'questions[{q_index}][answers][{answer_index}][text]' in request.data:
                        answer_data = {
                            'question': question.id,
                            'text': request.data[f'questions[{q_index}][answers][{answer_index}][text]'],
                            'is_correct': request.data.get(f'questions[{q_index}][answers][{answer_index}][is_correct]', '').lower() == 'true',
                        }

                        # Handle answer image
                        answer_image_key = f'questions[{q_index}][answers][{answer_index}][image]'
                        if answer_image_key in request.FILES:
                            answer_data['image'] = request.FILES[answer_image_key]

                        answer_serializer = AnswerSerializer(data=answer_data)
                        answer_serializer.is_valid(raise_exception=True)
                        answer_serializer.save()
                        answer_index += 1

                    created_questions.append(question)

                # Prepare response data
                response_data = self.get_serializer(created_questions, many=True).data
                if exam:
                    response_data = {
                        'exam_id': exam.id,
                        'questions': response_data
                    }

                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


#^ Answer
class AnswerListCreateView(generics.ListCreateAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question']


class AnswerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

#^ Essay Question
class EssaySubmissionListView(generics.ListAPIView):
    queryset = EssaySubmission.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = EssaySubmissionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['exam', 'student', 'question','result_trial']
    search_fields = ['student__name', 'exam__title']

class ScoreEssayQuestion(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Question.objects.all()
    
    def post(self, request, submission_id):
        # Fetch the essay submission
        essay_submission = get_object_or_404(EssaySubmission, pk=submission_id)

        # Validate and get the score from JSON request body
        try:
            score = float(request.data.get("score"))
            if score is None:
                return Response(
                    {"error": "Score is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate the score
            if score > essay_submission.question.points:
                return Response(
                    {
                        "error": f"Score must be less than or equal to {essay_submission.question.points}",
                        "max_points": essay_submission.question.points
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if score < 0:
                return Response(
                    {"error": "Score cannot be negative"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid score format. Must be a number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the essay submission
        essay_submission.score = score
        essay_submission.is_scored = True
        essay_submission.save()

        # Update the result and trial scores
        result = get_object_or_404(Result, student=essay_submission.student, exam=essay_submission.exam)
        trial = essay_submission.result_trial
        
        if trial:
            # Calculate scores
            mcq_score = Submission.objects.filter(
                result_trial=trial,
                is_correct=True
            ).aggregate(total=Sum('question__points'))['total'] or 0

            essay_score = EssaySubmission.objects.filter(
                result_trial=trial,
                is_scored=True
            ).aggregate(total=Sum('score'))['total'] or 0

            total_score = mcq_score + essay_score

            # Update scores
            trial.score = total_score
            trial.save()
            
            result.score = total_score
            result.save()

        # Response data
        response_data = {
            "message": "Essay question scored successfully",
            "submission": {
                "id": essay_submission.id,
                "student_id": essay_submission.student.id,
                "exam_id": essay_submission.exam.id,
                "question_id": essay_submission.question.id,
                "score": essay_submission.score,
                "max_score": essay_submission.question.points,
                "is_scored": essay_submission.is_scored
            },
            "updated_scores": {
                "trial_score": trial.score if trial else None,
                "result_score": result.score
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)



#^ Available Questions counts and statistics with different types and filters 
class QuestionCountView(APIView):
    """
    Endpoint to get the count of questions with details.
    Allows filtering by is_active, difficulty, category, lesson, unit, course, and question_type.
    """
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Question.objects.all()

    def get(self, request, *args, **kwargs):
        # Build filters dynamically
        filters = Q()

        # Extract filter parameters from the query
        is_active = request.query_params.get('is_active')
        category_id = request.query_params.get('category')
        lesson_id = request.query_params.get('lesson')
        unit_id = request.query_params.get('unit')
        course_id = request.query_params.get('course')
        question_type = request.query_params.get('question_type')

        # Apply filters if provided
        if is_active is not None:  # Explicit check for None as is_active is a boolean
            filters &= Q(is_active=(is_active.lower() == 'true'))

        if category_id:
            filters &= Q(category_id=category_id)

        if lesson_id:
            filters &= Q(lesson_id=lesson_id)

        if unit_id:
            filters &= Q(lesson__unit_id=unit_id)

        if course_id:
            filters &= Q(category__course_id=course_id)

        if question_type:
            filters &= Q(question_type=question_type)

        # Aggregate counts by difficulty and question type
        total_count = Question.objects.filter(filters).count()
        active_count = Question.objects.filter(filters & Q(is_active=True)).count()
        mcq_count = Question.objects.filter(filters & Q(question_type=QuestionType.MCQ)).count()
        essay_count = Question.objects.filter(filters & Q(question_type=QuestionType.ESSAY)).count()
        easy_count = Question.objects.filter(filters & Q(difficulty=DifficultyLevel.EASY)).count()
        medium_count = Question.objects.filter(filters & Q(difficulty=DifficultyLevel.MEDIUM)).count()
        hard_count = Question.objects.filter(filters & Q(difficulty=DifficultyLevel.HARD)).count()

        # Prepare response data
        response_data = {
            "count": total_count,
            "active_count": active_count,
            "mcq_count": mcq_count,
            "essay_count": essay_count,
            "easy_count": easy_count,
            "medium_count": medium_count,
            "hard_count": hard_count,
        }

        return Response(response_data, status=status.HTTP_200_OK)


#^ Exam Questions
class GetExamQuestions(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Exam.objects.all()

    def get(self, request, exam_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Check if the exam type is random
        if exam.type == ExamType.RANDOM:
            return Response(
                {"message": "Random exam, I'll pick its questions randomly."},
                status=status.HTTP_200_OK
            )

        # Fetch the questions related to the exam
        exam_questions = ExamQuestion.objects.filter(exam=exam).select_related('question')
        questions = [eq.question for eq in exam_questions]
        serializer = QuestionSerializer(questions, many=True)

        return Response(
            {
                "exam_id": exam.id,
                "exam_title": exam.title,
                "questions": serializer.data
            },
            status=status.HTTP_200_OK
        )


#^ add questions to an exam (manual and bank)
class AddBankExamQuestionsView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    parser_classes = [JSONParser]  # Use JSONParser to parse JSON data
    queryset = Question.objects.all()

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # Get the question IDs from the request
        question_ids = request.data.get("questions_ids", [])
        
        # Validate that question_ids is a list
        if not isinstance(question_ids, list):
            return Response(
                {"error": "Invalid format for question IDs. Expected a list of integers."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate the question IDs
        questions = Question.objects.filter(id__in=question_ids)
        invalid_ids = set(question_ids) - set(questions.values_list('id', flat=True))
        
        if invalid_ids:
            return Response(
                {"error": f"The following question IDs are invalid: {list(invalid_ids)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the questions to the exam
        added_questions = []
        skipped_questions = []
        
        for question in questions:
            # Use get_or_create to skip existing questions
            _, created = ExamQuestion.objects.get_or_create(exam=exam, question=question)
            if created:
                added_questions.append(question.id)
            else:
                skipped_questions.append(question.id)
        
        return Response(
            {
                "message": "Questions added to the exam successfully",
                "exam_id": exam.id,
                "exam_title": exam.title,
                "added_questions": added_questions,
                "skipped_questions": skipped_questions
            },
            status=status.HTTP_201_CREATED
        )


class AddManualExamQuestionsView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    parser_classes = [MultiPartParser, FormParser]
    queryset = Question.objects.all()
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, pk=exam_id)
        
        # if exam.type != ExamType.MANUAL:
        #     return Response(
        #         {"error": "This endpoint is only for manual-type exams"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # Extract question data
        question_data = request.data.dict()
        question_data['image'] = request.FILES.get('image', None)

        # Extract and structure answers
        answers = []
        index = 0
        while f'answers[{index}][text]' in request.data:
            answer = {
                'text': request.data[f'answers[{index}][text]'],
                'is_correct': request.data.get(f'answers[{index}][is_correct]', '').lower() == 'true',
            }
            if f'answers[{index}][image]' in request.FILES:
                answer['image'] = request.FILES[f'answers[{index}][image]']
            answers.append(answer)
            index += 1

        question_data['answers'] = answers

        # Use the QuestionSerializer to validate and create the question
        serializer = QuestionSerializer(data=question_data, context={'request': request})
        if serializer.is_valid():
            question = serializer.save()
            ExamQuestion.objects.create(exam=exam, question=question)
            return Response(
                {"message": "Questions successfully created and added to the exam"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveExamQuestion(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Question.objects.all()
    def delete(self, request, exam_id, question_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Fetch the exam question
        exam_question = get_object_or_404(
            ExamQuestion,
            exam=exam,
            question_id=question_id,
            is_active=True
        )

        # Remove the question from the exam (mark it as inactive)
        exam_question.delete()

        return Response(
            {"success": "Question removed from exam"},
            status=status.HTTP_200_OK
        )


#^ add questions to RandomExamBank (the small bank of questions selected for a random exam to create the models of them)
class GetRandomExamBank(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def get(self, request, exam_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Validate exam type
        if exam.type != ExamType.RANDOM:
            return Response(
                {"error": "This endpoint is only for random type exams"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the random exam bank
        random_exam_bank = get_object_or_404(RandomExamBank, exam=exam)
        serializer = RandomExamBankSerializer(random_exam_bank)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AddToRandomExamBank(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def post(self, request, exam_id):
        # Fetch the exam
        exam = get_object_or_404(Exam, pk=exam_id)

        # Validate exam type
        if exam.type != ExamType.RANDOM:
            return Response(
                {"error": "This endpoint is only for random type exams"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate question IDs
        question_ids = request.data.get("question_ids", [])
        questions = Question.objects.filter(id__in=question_ids)

        if len(questions) != len(question_ids):
            return Response(
                {"error": "Some question IDs are invalid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add questions to the random exam bank
        random_exam_bank, created = RandomExamBank.objects.get_or_create(exam=exam)
        random_exam_bank.questions.add(*questions)

        return Response(
            {"message": "Questions successfully added to the random exam bank"},
            status=status.HTTP_201_CREATED
        )

#^ ExamModels
class ExamModelListCreateView(generics.ListCreateAPIView):
    queryset = ExamModel.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ExamModelSerializer
    filterset_fields = ['is_active', 'exam']


class ExamModelRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExamModel.objects.all()
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ExamModelSerializer

#^ get examModel questions (he already added questions , to be reviewed by admin )
class GetExamModelQuestions(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def get(self, request, exam_model_id):
        # Fetch the exam model
        exam_model = get_object_or_404(ExamModel, pk=exam_model_id)

        # Fetch active questions for the exam model
        questions = [mq.question for mq in exam_model.model_questions.all()]

        # Serialize the questions
        serializer = QuestionSerializer(questions, many=True)

        # Return the response
        return Response(
            {
                "exam_model_id": exam_model.id,
                "exam_model_title": exam_model.title,
                "questions": serializer.data
            },
            status=status.HTTP_200_OK
        )


#^ Remove Question from an ExamModel
class RemoveQuestionFromExamModel(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def delete(self, request, exam_model_id, question_id):
        try:
            exam_model = get_object_or_404(ExamModel, pk=exam_model_id)
            question = get_object_or_404(Question, pk=question_id)
            exam_model_question = get_object_or_404(ExamModelQuestion, exam_model=exam_model, question=question)
            exam_model_question.delete()
            return Response(
                {"message": "Question successfully removed from the exam model"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#^ get : gets questions (randomly) from the RandomExamBank related to that exam so the teacher reviews them and modify or delete some (using other endpoints we already have)
class SuggestQuestionsForModel(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def get_random_questions(self, exam: Exam, related_questions: QuerySet) -> List[Question]:
        """
        Get random questions based on the exam's difficulty distribution.
        """
        if (
            exam.easy_questions_count == 0
            and exam.medium_questions_count == 0
            and exam.hard_questions_count == 0
        ):
            # If no difficulty distribution is specified, return random questions
            if related_questions.count() < exam.number_of_questions:
                raise ValidationError(
                    f"Not enough questions available for {exam.related_to.lower()} '{exam.get_related_name()}'"
                )
            return list(related_questions.order_by('?')[:exam.number_of_questions])

        questions = []
        for difficulty, count in [
            ("EASY", exam.easy_questions_count),
            ("MEDIUM", exam.medium_questions_count),
            ("HARD", exam.hard_questions_count)
        ]:
            if count > 0:
                difficulty_questions = related_questions.filter(difficulty=difficulty)

                if difficulty_questions.count() < count:
                    raise ValidationError(
                        f"Not enough {difficulty} questions in the bank related to the "
                        f"{exam.related_to.lower()} '{exam.get_related_name()}'."
                    )

                questions.extend(list(difficulty_questions.order_by('?')[:count]))

        return questions

    def get_related_questions(self, exam: Exam) -> QuerySet:
        """
        Get the related questions from the random exam bank.
        """
        random_exam_bank = RandomExamBank.objects.filter(exam=exam).first()
        if not random_exam_bank:
            raise ValidationError("No Available Random Bank for that Exam, please create one first.")
        return random_exam_bank.questions.all()

    def get(self, request, exam_id):
        try:
            # Fetch the exam
            exam = get_object_or_404(Exam, pk=exam_id)

            # Validate exam type
            if exam.type != ExamType.RANDOM:
                return Response(
                    {"error": "This endpoint is only for random type exams"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get related questions from the random exam bank
            related_questions = self.get_related_questions(exam)

            # Validate if there are enough questions
            if related_questions.count() < exam.number_of_questions:
                raise ValidationError(
                    f"Not enough questions available for {exam.related_to.lower()} '{exam.get_related_name()}'"
                )

            # Get random questions based on the exam's difficulty distribution
            random_questions = self.get_random_questions(exam, related_questions)

            # Serialize the questions
            serializer = QuestionSerializer(random_questions, many=True)

            # Return the response
            return Response({
                "exam_id": exam.id,
                "exam_title": exam.title,
                "questions": serializer.data
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# post : receives the reviewed suggestions and modified questions to store them in the ExamModelQuestion )
class AddQuestionsToModel(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ExamModel.objects.all()
    def post(self, request, exam_id, exam_model_id):
        try:
            # Get the Exam and ExamModel objects
            exam = get_object_or_404(Exam, pk=exam_id)
            exam_model = get_object_or_404(ExamModel, pk=exam_model_id, exam=exam)

            # Validate exam type
            if exam.type != ExamType.RANDOM:
                return Response(
                    {"error": "This endpoint is only for random type exams"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the question IDs from the request
            question_ids = request.data.get("question_ids", [])

            # Validate the question IDs
            questions = Question.objects.filter(id__in=question_ids)
            invalid_ids = set(question_ids) - set(questions.values_list('id', flat=True))
            if invalid_ids:
                return Response(
                    {"error": f"The following question IDs are invalid: {list(invalid_ids)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Add the questions to the ExamModel
            added_questions = []
            skipped_questions = []
            for question in questions:
                # Use get_or_create to skip existing questions
                _, created = ExamModelQuestion.objects.get_or_create(exam_model=exam_model, question=question)
                if created:
                    added_questions.append(question.id)
                else:
                    skipped_questions.append(question.id)

            return Response({
                "message": "Questions added to the exam model successfully",
                "model_id": exam_model.id,
                "title": exam_model.title,
                "added_questions": added_questions,
                "skipped_questions": skipped_questions
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






#^ Results
class ResultListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ResultSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter] 
    filterset_fields = ['student', 'exam', 'exam__unit', 'exam__lesson', 'exam__related_to']
    search_fields = ['student__name', 'student__user__username', 'exam__title', 'exam__description']
    queryset = ExamModel.objects.all()
    def get_queryset(self):
        results = Result.objects.all().select_related(
            'exam', 'student', 'exam_model'
        ).prefetch_related(
            'trials', 'exam__submissions', 'exam__exam_questions', 'exam_model__exam_model_questions'
        ).annotate(
            total_questions=Count('exam__exam_questions'),
            is_allowed_to_show_result=Case(
                When(exam__allow_show_results_at__lte=timezone.now(), then=True),
                default=False,
                output_field=BooleanField()
            )
        )
        return results


class ReduceResultTrialView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    
    def post(self, request, result_id):
        result = get_object_or_404(Result, pk=result_id)
        
        if result.trial == 0:
            return Response(
                {"error": "No trials exist for this result."},
                status=status.HTTP_400_BAD_REQUEST
            )

        last_trial = result.trials.filter(trial=result.trial).first()
        if not last_trial:
            return Response(
                {"error": "No trial found for the current trial count."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Delete related submissions and essay submissions
            Submission.objects.filter(result_trial=last_trial).delete()
            EssaySubmission.objects.filter(result_trial=last_trial).delete()
            
            last_trial.delete()
            result.trial -= 1

            if result.trial == 0:
                result.delete()
                return Response(
                    {"message": "Trial reduced successfully. Result deleted as trial count reached zero."},
                    status=status.HTTP_200_OK
                )

            result.save()

        return Response(
            {"message": "Trial reduced successfully.", "new_trial_count": result.trial},
            status=status.HTTP_200_OK
        )


class ExamResultDetailView(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = Result.objects.all()  # Add this line if you choose the queryset approach

    def get(self, request, result_id):
        result = get_object_or_404(Result, pk=result_id)
        active_trial = result.active_trial

        # Fetch both MCQ and Essay submissions
        mcq_submissions = Submission.objects.filter(
            result_trial=active_trial
        ).select_related('question', 'selected_answer', 'question__category')

        essay_submissions = EssaySubmission.objects.filter(
            result_trial=active_trial
        ).select_related('question', 'question__category')

        student_answers = []
        unsolved_questions = []
        unscored_essay_questions = []  # New list for unscored essay questions

        # Process MCQ submissions
        for submission in mcq_submissions:
            question = submission.question
            answer_data = self._build_mcq_answer_data(submission, question)
            student_answers.append(answer_data)
            if not submission.is_solved:
                unsolved_questions.append(answer_data)

        # Process Essay submissions
        for submission in essay_submissions:
            question = submission.question
            answer_data = self._build_essay_answer_data(submission, question)
            student_answers.append(answer_data)
            if not submission.is_scored:
                unscored_essay_questions.append(answer_data)  # Add to unscored_essay_questions

        # Fetch correct answers and questions
        questions = Question.objects.filter(
            exam_questions__exam=result.exam
        ).select_related('category').prefetch_related('answers').distinct()

        correct_answers = [self._build_correct_answer_data(q) for q in questions]

        # Fetch all trials
        trials = result.trials.all().order_by('trial')
        trial_data = [{
            "trial_number": trial.trial,
            "score": trial.score,
            "exam_score": trial.exam_score,
            "student_started_exam_at": trial.student_started_exam_at,
            "student_submitted_exam_at": trial.student_submitted_exam_at,
            "submit_type": trial.submit_type,
        } for trial in trials]

        response_data = {
            "student_id": result.student.id,
            "student_name": result.student.name,
            "exam_id": result.exam.id,
            "exam_title": result.exam.title,
            "exam_description": result.exam.description,
            "exam_score": active_trial.exam_score if active_trial else 0,
            "student_score": active_trial.score if active_trial else 0,
            "is_succeeded": result.is_succeeded,
            "student_trials": result.trial,
            "is_trials_finished": result.is_trials_finished,
            "student_answers": student_answers,
            "unsolved_questions": unsolved_questions,
            "unscored_essay_questions": unscored_essay_questions,  # Include in response
            "correct_answers": correct_answers,
            "trials": trial_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def _build_mcq_answer_data(self, submission, question):
        return {
            "type": "mcq",
            "question_id": question.id,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "category_title": question.category.title if question.category else None,
            "category_id": question.category.id if question.category else None,
            "selected_answer": submission.selected_answer.text if submission.selected_answer else None,
            "selected_answer_id": submission.selected_answer.id if submission.selected_answer else None,
            "is_correct": submission.is_correct,
            "is_solved": submission.is_solved,
            "points": question.points,
        }

    def _build_essay_answer_data(self, submission, question):
        return {
            "type": "essay",
            "question_id": question.id,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "category_title": question.category.title if question.category else None,
            "category_id": question.category.id if question.category else None,
            "answer_text": submission.answer_text,
            "answer_file": submission.answer_file.url if submission.answer_file else None,
            "score": submission.score,
            "is_scored": submission.is_scored,
            "points": question.points,
            "max_points": question.points,
        }

    def _build_correct_answer_data(self, question):
        return {
            "question_id": question.id,
            "question_text": question.text,
            "question_image": question.image.url if question.image else None,
            "category_title": question.category.title if question.category else None,
            "category_id": question.category.id if question.category else None,
            "correct_answers": [
                {
                    "text": answer.text,
                    "image": answer.image.url if answer.image else None,
                    "is_correct": answer.is_correct
                }
                for answer in question.answers.all()  # Show all answers but indicate correct ones
            ],
            "question_type": question.question_type,
        }


class ResultTrialsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    serializer_class = ResultTrialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['submit_type']

    def get_queryset(self):
        result_id = self.kwargs['result_id']
        result = get_object_or_404(Result, id=result_id)
        return result.trials.all().annotate(
            mcq_score=Sum('submissions__question__points', filter=models.Q(submissions__is_correct=True)),
            essay_score=Sum('essay_submissions__score', filter=models.Q(essay_submissions__is_scored=True))
        ).order_by('trial')








#^ get students who toke the exam and those who didn't
class StudentsTookExamAPIView(generics.ListAPIView):
    serializer_class = CombinedStudentResultSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = ResultTrial.objects.all()
    
    def get_queryset(self):
        exam_id = self.kwargs['exam_id']
        exam = get_object_or_404(Exam, id=exam_id)

        # Get the related course for the exam
        related_course_id = exam.get_related_course()
        if not related_course_id:
            return Response({"error": "Exam is not related to any course"}, status=status.HTTP_400_BAD_REQUEST)

        # Get students who are subscribed to the related course
        subscribed_students = Student.objects.all()
        # subscribed_students = Student.objects.filter(
        #     coursesubscription__course_id=related_course_id,
        #     coursesubscription__active=True
        # ).distinct()

        # Filter by student.by_code if the query parameter is provided
        by_code_filter = self.request.query_params.get('by_code', None)
        if by_code_filter is not None:
            by_code_filter = by_code_filter.lower() == 'true'  # Convert to boolean
            subscribed_students = subscribed_students.filter(by_code=by_code_filter)

        # Get students who took the exam (from the subscribed students)
        students_took_exam = subscribed_students.filter(result__exam=exam).distinct()

        # Search functionality
        search_query = self.request.query_params.get('search', None)
        if search_query:
            students_took_exam = students_took_exam.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(parent_phone__icontains=search_query) |
                Q(government__icontains=search_query)
            )

        # Prefetch related Result and ResultTrial data
        students_took_exam = students_took_exam.prefetch_related(
            Prefetch('result_set', queryset=Result.objects.filter(exam=exam).prefetch_related('trials'))
        )

        return students_took_exam


class StudentsDidNotTakeExamAPIView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    

    def get_queryset(self):
        exam_id = self.kwargs['exam_id']
        exam = get_object_or_404(Exam, id=exam_id)

        # Get the related course for the exam
        related_course_id = exam.get_related_course()
        if not related_course_id:
            return Response({"error": "Exam is not related to any course"}, status=status.HTTP_400_BAD_REQUEST)

        # Get students who are subscribed to the related course
        subscribed_students = Student.objects.filter(
            coursesubscription__course_id=related_course_id,
            coursesubscription__active=True
        ).distinct()

        # Filter by student.by_code if the query parameter is provided
        by_code_filter = self.request.query_params.get('by_code', None)
        if by_code_filter is not None:
            by_code_filter = by_code_filter.lower() == 'true'  # Convert to boolean
            subscribed_students = subscribed_students.filter(by_code=by_code_filter)

        # Get students who didn't take the exam (from the subscribed students)
        students_did_not_take_exam = subscribed_students.exclude(result__exam=exam).distinct()

        # Search functionality
        search_query = self.request.query_params.get('search', None)
        if search_query:
            students_did_not_take_exam = students_did_not_take_exam.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(parent_phone__icontains=search_query) |
                Q(government__icontains=search_query)
            )

        return students_did_not_take_exam


class ExamsTakenByStudentAPIView(generics.ListAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def get_queryset(self):
        student_id = self.kwargs['student_id']
        student = get_object_or_404(Student, id=student_id)

        # Get exams taken by the student (using the related_name 'results' in the Result model)
        exams_taken = Exam.objects.filter(results__student=student).distinct()

        # Search functionality (optional, if needed)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            exams_taken = exams_taken.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return exams_taken

    def list(self, request, *args, **kwargs):
        # Get the queryset
        queryset = self.get_queryset()

        # Serialize the exams
        exam_serializer = self.get_serializer(queryset, many=True)
        exam_data = exam_serializer.data

        # Get the student ID from the URL
        student_id = self.kwargs['student_id']

        # Add result data for each exam
        for exam in exam_data:
            # Get the result for the current student and exam
            result = Result.objects.filter(student_id=student_id, exam_id=exam['id']).prefetch_related('trials').first()
            if result:
                # Serialize the result
                result_serializer = BriefedResultSerializer(result)
                exam['result'] = result_serializer.data
            else:
                exam['result'] = None

        # Return the response
        return Response(exam_data, status=status.HTTP_200_OK)


class ExamsNotTakenByStudentAPIView(generics.ListAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]

    def get_queryset(self):
        student_id = self.kwargs['student_id']
        student = get_object_or_404(Student, id=student_id)
        
        # Get active course subscriptions for the student
        student_course_subscriptions = CourseSubscription.objects.filter(
            student=student, 
            active=True
        )
        
        # Get the IDs of subscribed courses
        subscribed_course_ids = student_course_subscriptions.values_list('course_id', flat=True)
        
        # Get exams from subscribed courses only
        subscribed_exams = Exam.objects.filter(
            Q(unit__course_id__in=subscribed_course_ids) | 
            Q(lesson__unit__course_id__in=subscribed_course_ids)
        ).distinct()
        
        # Get exams taken by the student
        exams_taken = Exam.objects.filter(results__student=student).distinct()
        
        # Get exams not taken by the student (from subscribed courses only)
        exams_not_taken = subscribed_exams.exclude(id__in=exams_taken.values('id'))
        
        # Search functionality (optional, if needed)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            exams_not_taken = exams_not_taken.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        return exams_not_taken


class CopyExamView(APIView):
    def post(self, request, exam_id):
        serializer = CopyExamSerializer(data=request.data)
        if serializer.is_valid():
            original_exam = Exam.objects.get(pk=exam_id)
            data = serializer.validated_data

            # Create a copy
            new_exam = Exam.objects.create(
                title=original_exam.title,
                description=original_exam.description,
                related_to=data['related_to'],
                unit=data.get('unit'),
                lesson=data.get('lesson'),
                course=data['course'],
                number_of_questions=original_exam.number_of_questions,
                time_limit=original_exam.time_limit,
                score=original_exam.score,
                passing_percent=original_exam.passing_percent,
                start=original_exam.start,
                end=original_exam.end,
                number_of_allowed_trials=original_exam.number_of_allowed_trials,
                type=original_exam.type,
                easy_questions_count=original_exam.easy_questions_count,
                medium_questions_count=original_exam.medium_questions_count,
                hard_questions_count=original_exam.hard_questions_count,
                show_answers_after_finish=original_exam.show_answers_after_finish,
                order=original_exam.order,
                is_active=original_exam.is_active,
                allow_show_results_at=original_exam.allow_show_results_at,
                allow_show_answers_at=original_exam.allow_show_answers_at,
                is_depends=original_exam.is_depends,
            )

            # Copy exam questions
            for eq in original_exam.exam_questions.all():
                ExamQuestion.objects.create(
                    exam=new_exam,
                    question=eq.question,
                    is_active=eq.is_active
                )

            return Response({"id": new_exam.id, "message": "Exam copied successfully."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#ap:Mobile
#^ < ==============================[ <- Mobile App -> ]============================== > ^#

class AppValidationData(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get("course_id")
        lesson_id = request.data.get("lesson_id")
        # check if the app last version
        """""
        build_number = str(request.data.get("build_number"))
        app_version = str(request.data.get("app_version"))

        if build_number != settings.BUILD_NUMBER or app_version != settings.APP_VERSION:
            return Response(
                {"message": "Please update the app to the latest version"},
                status=status.HTTP_426_UPGRADE_REQUIRED
            )
        """""


        # Validate required parameters
        if not course_id or not lesson_id:
            return Response(
                {"error": "course_id and lesson_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = get_object_or_404(Course, id=course_id)
        student = request.user.student

        # Verify subscription
        if not self._has_active_subscription(student, course):
            return Response(
                {"error": "You do not have access permissions"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Access lesson and handle response
        lesson_response = self._access_lesson(course, lesson_id, student)
        if lesson_response:
            return lesson_response

        return Response({"message": "Lesson access granted"}, status=status.HTTP_200_OK)

    def _has_active_subscription(self, student, course):
        course_subscription = CourseSubscription.objects.filter(
            student=student, course=course, active=True
        ).exists()

        lesson_subscription = LessonSubscription.objects.filter(
            student=student, lesson__unit__course=course, active=True
        ).exists()

        return course_subscription or lesson_subscription


    def _access_lesson(self, course, lesson_id, student):
        """
        Handle lesson access logic.
        """
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Validate that the lesson belongs to the course
        if lesson.unit.course != course:
            return Response(
                {"error": "This lesson does not belong to the specified course"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the lesson is pending
        if lesson.pending:
            return Response(
                {"error": "This lesson is pending and unavailable"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if the student has exceeded the allowed views
        lesson_view, _ = LessonView.objects.get_or_create(student=student, lesson=lesson)
        if lesson_view.counter >= lesson.view:
            return Response(
                {"error": "You do not have remaining views for this lesson"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None 

#ap:Codes
#^ < ==============================[ <- Codes -> ]============================== > ^#

class GenerateStudentCodes(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentCode.objects.all()
    def post(self,request,*args, **kwargs):
        quantity = int(request.data.get("quantity"))
        codes = []
        for _ in range(quantity):
            code = StudentCode.objects.create() 
            code.save()
            codes.append(code.code)
        return Response({"codes":codes},status=status.HTTP_200_OK)


class GenerateCourseCodes(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentCode.objects.all()

    def post(self,request,*args, ** kwargs):
        quantity = int(request.data.get("quantity"))
        price = request.data.get("price")
        course_id = request.data.get("course_id")
        code_title = request.data.get("title")
        codes = []
        for _ in range(quantity):
            code = CourseCode.objects.create(course_id=course_id)
            code.title = code_title
            code.price = price
            code.save()
            codes.append(code.code)
        return Response({"codes":codes},status=status.HTTP_201_CREATED)


class GenerateLessonCodes(APIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentCode.objects.all()

    def post(self,request,*args, ** kwargs):
        quantity = int(request.data.get("quantity"))
        price = request.data.get("price")
        lesson_id = request.data.get("lesson_id")
        course_id = request.data.get("course_id",None)
        codes = []
        
        if course_id:
            course = get_object_or_404(Course,id=course_id)
            for _ in range(quantity):
                code = AnyLessonCode.objects.create(course=course,price=price)
                code.save()
                codes.append(code.code)
            return Response({"codes":codes},status=status.HTTP_201_CREATED)
        
        
        for _ in range(quantity):
            code = LessonCode.objects.create(lesson_id=lesson_id,price=price)
            code.save()
            codes.append(code.code)
        return Response({"codes":codes},status=status.HTTP_201_CREATED)



class CourseCodeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = CourseCode.objects.all().order_by("-created")
    serializer_class = CourseCodeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['course','available']
    search_fields = ['title', 'code','student__user__username']


class StudentCodeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = StudentCode.objects.all().order_by("-created")
    serializer_class = StudentCodeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['available']
    search_fields = ['student__user__username']


class LessonCodeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = LessonCode.objects.all().order_by("-created")
    serializer_class = LessonCodeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['lesson','available']
    search_fields = ['code','student__user__username']


class ListPromoCode(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]
    queryset =  PromoCode.objects.all().order_by("-created")
    serializer_class = ListPromoCodeSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = [
            'course',
            'usage_limit',
            'used_count',
            'is_active',
            ]

    search_fields = [
        'code',
        ]


class CreatePromoCode(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = PromoCode.objects.all()
    serializer_class = ListPromoCodeSerializer


class UpdatePromoCode(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, CustomDjangoModelPermissions]
    queryset = PromoCode.objects.all()
    serializer_class = ListPromoCodeSerializer
    lookup_field = 'id'  


#ap:ExtraApp
#^ < ==============================[ <- ExtraApp -> ]============================== > ^#

# List view
class NewsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]  
    queryset = News.objects.all().order_by("-created")
    serializer_class = NewsSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    
    filterset_fields = [
        'year',
        ]

# Create view
class NewsCreateView(generics.CreateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save()

# Update view
class NewsUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions] 
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    lookup_field = 'id'  

# Delete view
class NewsDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions] 
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    lookup_field = 'id'


class UpdateListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated,CustomDjangoModelPermissions]  
    queryset = Update.objects.all().order_by("-created")
    serializer_class = UpdateSerializer

#ap:Permissions
#^ < ==============================[ <- Permissions -> ]============================== > ^#

class PermissionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = ['content_type__model',]


class AddPermissionsToUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Permission.objects.all()
    
    def post(self, request):
        username = request.data.get('username')
        permissions = request.data.get('permissions', [])

        if not username:
            return Response(
                {"error": "Username is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the user
            user = User.objects.get(username=username)

            if permissions == []:
                # Remove all permissions if the list is empty
                user.user_permissions.clear()
                return Response({"message": "All permissions removed successfully!"})

            # Remove permissions not in the provided list
            current_permissions = user.user_permissions.all()
            current_codenames = [perm.codename for perm in current_permissions]

            # Revoke permissions not in the input list
            for perm_codename in current_codenames:
                if perm_codename not in permissions:
                    perm = Permission.objects.get(codename=perm_codename)
                    user.user_permissions.remove(perm)

            # Add the provided permissions
            for perm_codename in permissions:
                if perm_codename not in current_codenames:
                    perm = Permission.objects.get(codename=perm_codename)
                    user.user_permissions.add(perm)

            user.save()
            return Response({"message": "Permissions updated successfully!"})

        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Permission.DoesNotExist:
            return Response(
                {"error": "One or more permissions not found."},
                status=status.HTTP_404_NOT_FOUND
            )


#ap:Extra
#^ < ==============================[ <- Extra -> ]============================== > ^#

class ExtraCourseList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,*args, ** kwargs):
        qr = Course.objects.values("id",'name')
        return Response(qr,status=status.HTTP_200_OK)


class ExtraUnitList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,course_id,*args, ** kwargs):
        qr = Unit.objects.filter(course_id=course_id).values("id",'name')
        return Response(qr,status=status.HTTP_200_OK)


class ExtraLessonList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,unit_id,*args, ** kwargs):
        qr = Lesson.objects.filter(unit_id=unit_id).values("id",'name')
        return Response(qr,status=status.HTTP_200_OK)


#^ < ==============================[ <- Logs -> ]============================== > ^#

class RequestLogListView(generics.ListAPIView):
    queryset = RequestLog.objects.all()
    serializer_class = RequestLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = RequestLogFilter 
    search_fields = ['path', 'view_name']
    ordering_fields = ['timestamp', 'response_time', 'status_code']
    ordering = ['-timestamp']

class RequestLogDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date and not end_date:
            return Response(
                {"error": "At least one of start_date or end_date must be provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start building the query
        query_filter = {}
        
        # Process start_date if provided
        if start_date:
            try:
                # Try to parse as ISO datetime first
                start_datetime = parse_datetime(start_date)
                
                # If that fails, try to parse as date only
                if not start_datetime:
                    date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                    start_datetime = timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time.min))
                
                # If it's still None, it's an invalid format
                if not start_datetime:
                    return Response(
                        {"error": "Invalid start_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                query_filter['timestamp__gte'] = start_datetime
                
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Process end_date if provided
        if end_date:
            try:
                # Try to parse as ISO datetime first
                end_datetime = parse_datetime(end_date)
                
                # If that fails, try to parse as date only
                if not end_datetime:
                    date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                    end_datetime = timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time.max))
                
                # If it's still None, it's an invalid format
                if not end_datetime:
                    return Response(
                        {"error": "Invalid end_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                query_filter['timestamp__lte'] = end_datetime
                
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use ISO format (YYYY-MM-DDThh:mm:ss) or YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Debug info before deletion
        logs_before_delete = RequestLog.objects.filter(**query_filter).count()
        
        # Delete logs
        deleted, _ = RequestLog.objects.filter(**query_filter).delete()
        
        # Add debug info to response
        return Response({
            "message": f"Successfully deleted {deleted} logs",
            "deleted_count": deleted,
            "found_before_delete": logs_before_delete,
            "query_filter": {
                "start_date": str(query_filter.get('timestamp__gte')),
                "end_date": str(query_filter.get('timestamp__lte'))
            }
        })







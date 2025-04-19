import requests
import hashlib
import json
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError
from student.models import Student
from course.models import Course,CourseCollection,CourseCollectionCode,LessonCode,AnyLessonCode,CourseCode,Lesson
from subscription.models import CourseSubscription
from .models import Invoice,PromoCode
from django.conf import settings
from datetime import timedelta , datetime
from .utils import generate_sequence

# Create your views here.

#*============================>Course<============================#*

class PayWithCenterCode(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get("course_id")
        code = request.data.get("course_code")
        student = request.user.student
        get_code = get_object_or_404(CourseCode,code=code,student=None)
        get_course = get_object_or_404(Course, id=course_id)
        
        if get_code.course.id != get_course.id or get_code.student:
            raise ValidationError({"detail": "The course code does not match the  course in code or not valid"})
        
        # Check if student not code and course is center
        if get_course.center and not student.by_code:
            raise ValidationError({"error":"this course is center"})
        
        # Create invoice
        create = Invoice.objects.create(
            student=student,
            course=get_code.course,
            pay_status="C",
            pay_method="C",
            code = get_code.code,
            price = get_code.price,
            pay_at = timezone.now(),
            expires_at = timezone.now(),
        )

        # Update any existing pending invoices for this student and course to expired
        Invoice.objects.filter(student=student, course=get_code.course, pay_status='P').update(
            pay_status='E',
            expires_at=timezone.now()
        )
        get_code.student = student
        get_code.available = False
        get_code.save()
        return Response(status=status.HTTP_200_OK)

class FreeCourse(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,*args, **kwargs):
        course_id = request.data.get("course_id")
        get_course = get_object_or_404(Course,id=course_id)
        student = request.user.student
        # Check if student not code and course is center
        if get_course.center and not student.by_code:
            return ValidationError({"error":"this course is center"},status=status.HTTP_400_BAD_REQUEST)
        
        if get_course.free or get_course.price == 0:
            new_invoice = Invoice.objects.create(
                student=student,
                course=get_course,
                price=get_course.price,
                free=True,
                pay_status='C',
                pay_method='R',
                expires_at=timezone.now(),
                pay_at=timezone.now(),
            )

        else:
            return ValidationError({"error":"this course is not free"},status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)

class GetPromoCodeDiscount(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        code_text = request.query_params.get("code") 
        course_data = {}
        if not code_text:
            return Response({"error": "Promo code is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        get_promo_code = get_object_or_404(PromoCode, code=code_text)
        if get_promo_code.course:
            course_data = {
                get_promo_code.name
            }

            
        context = {
            "course": get_promo_code.course,
            "expiration_date": get_promo_code.expiration_date,
            "discount_percent": get_promo_code.discount_percent,
            **course_data
        }
        return Response(context, status=status.HTTP_200_OK)


#*============================>Fawry<============================#*

class PayWithFawry(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        course_id = request.data.get("course_id")
        promo_code = request.data.get("promo_code")
        promo = None
        apply_promo_code = False
        student = request.user.student
        get_course = get_object_or_404(Course, id=course_id)

        # Check if student is not using a code and course is center
        if get_course.center and not student.by_code:
            return Response({"error": "This course is center."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for an existing valid invoice
        existing_invoice = Invoice.objects.filter(
            student=student,
            course=get_course,
            pay_status='P',
            expires_at__gt=timezone.now()
        ).first()

        if existing_invoice:
            return Response({
                "id_invoice": existing_invoice.id,
                "referenceNumber": existing_invoice.fawry_reference_number,
                "course_price": get_course.price,
                "apply_promo_code": bool(existing_invoice.promo_code),
                "amount": existing_invoice.price,
                "expires_at": existing_invoice.expires_at
            }, status=200)

        # Determine course price
        amount = get_course.price

        # Validate promo code if provided
        if promo_code:
            promo = PromoCode.objects.filter(code=promo_code).first()
            
            if not promo:
                return Response({"error": "Invalid promo code."}, status=status.HTTP_400_BAD_REQUEST)

            if not promo.is_valid():
                return Response({"error": "Promo code is not valid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the student has already used the promo code
            if promo.used_by_students.filter(id=student.id).exists():
                return Response({"error": "You have already used this promo code."}, status=status.HTTP_400_BAD_REQUEST)
            
            if promo.course and promo.course != get_course:
                return Response({"error": "This promo code is not valid for the selected course."}, status=status.HTTP_400_BAD_REQUEST)

            # Apply discount
            discount = (promo.discount_percent / 100) * amount
            amount -= discount
            promo.used_count += 1
            promo.used_by_students.add(student)
            promo.save()
            apply_promo_code = True
            
        # Ensure amount is a valid decimal
        amount = f"{amount:.2f}"

        # ^ Fawry payment integration

        fawry_url = settings.FAWRY_URL
        merchant_code = settings.MERCHANT_CODE
        merchant_sec_key = settings.MERCHANT_SEC_KEY
        payment_method = 'PAYATFAWRY'
        payment_expiry = settings.FAWRY_PAYMENT_EXPIRY

        # Generate a unique reference number
        merchant_ref_num = generate_sequence()
        student_profile_id = student.id

        # Concatenate and encode the string for hashing
        data_to_hash = f"{merchant_code}{merchant_ref_num}{student_profile_id}{payment_method}{amount}{merchant_sec_key}"
        signature = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

        payment_data = {
            'merchantCode': merchant_code,
            'merchantRefNum': merchant_ref_num,
            'customerName': student.name,
            'customerMobile': student.user.username,
            'customerEmail': 'EasyTech@gmail.com',
            'customerProfileId': student_profile_id,
            'amount': amount,
            'paymentExpiry': str(payment_expiry),
            'currencyCode': 'EGP',
            'language': 'en-gb',
            'chargeItems': [
                {
                    'itemId': get_course.id,
                    'description': get_course.description,
                    'price': amount,
                    'quantity': '1'
                }
            ],
            'signature': signature,
            'paymentMethod': payment_method,
            'description': f'Payment for course - {get_course.name}',
        }

        # Sending the POST request and saving the response
        response = requests.post(url=fawry_url, json=payment_data)
        response_data = response.json()

        # Create Invoice
        new_invoice = Invoice.objects.create(
            student=student,
            course=get_course,
            sequence=merchant_ref_num,
            price=amount,
            pay_method="F",
            pay_status='P',
            fawry_reference_number=response_data['referenceNumber'],
            fawry_signature=signature,
            expires_at=datetime.fromtimestamp(payment_expiry / 1000).strftime('%Y-%m-%d %H:%M:%S')
        )

        if apply_promo_code:
            new_invoice.promo_code = promo
            new_invoice.save()
            promo_code_context = {
                "promo_discount_percent": promo.discount_percent,
                "promo_code": promo.code,
            }
        else:
            promo_code_context = {}

        context = {
            "id_invoice": new_invoice.id,
            "referenceNumber": response_data['referenceNumber'],
            "course_price": get_course.price,
            "apply_promo_code": apply_promo_code,
            "amount": amount,
            "expires_at": new_invoice.expires_at,
            **promo_code_context
        }

        return Response(context, status=200)


class FawryCallBack(APIView):
    def post(self, request, api_key , *args, **kwargs):
        the_key = "41436efb-dcc4-4f15-adea-42d0a0f45491"
        
        if api_key != the_key:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        response_data = request.data

        if response_data.get("orderStatus") == "PAID" :
            fawry_ref_number = response_data.get("fawryRefNumber")
            pay_at = int(response_data.get("paymentTime"))
            
            payment_time_sec = pay_at / 1000
            pay_at_convert = datetime.utcfromtimestamp(payment_time_sec)

            get_invoice = get_object_or_404( Invoice , fawry_reference_number=fawry_ref_number)
            get_invoice.pay_status = "C"
            get_invoice.pay_at = pay_at_convert
            get_invoice.save()
    
        return Response(status=status.HTTP_200_OK)

#*============================>Course Collection<============================#*

class PayCourseCollectionWithCenterCode(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        collection_id = request.data.get("collection_id")
        collection_code = request.data.get("collection_code")
        student = request.user.student
        get_code = get_object_or_404(CourseCollectionCode,code=collection_code,student=None)
        get_course_collection = get_object_or_404(CourseCollection, id=collection_id)
        
        if get_code.collection.id != get_course_collection.id or get_code.student:
            raise ValidationError({"detail": "The course code does not match the  course in code or not valid"})
        
        # Check if student not code and course is center
        if get_course_collection.center and not student.by_code:
            return ValidationError({"error":"this course is center"},status=status.HTTP_400_BAD_REQUEST)
        
        # Create invoice
        create = Invoice.objects.create(
            student=student,
            course_collection=get_code.collection,
            pay_status="C",
            pay_method="C",
            code = get_code.code,
            price = get_code.price,
            pay_at = timezone.now(),
            expires_at = timezone.now(),
        )

        # Update any existing pending invoices for this student and course to expired
        Invoice.objects.filter(student=student, course_collection=get_code.collection, pay_status='P').update(
            pay_status='E',
            expires_at=timezone.now()
        )
        get_code.student = student
        get_code.available = False
        get_code.save()

        
        return Response(status=status.HTTP_200_OK)


#*============================>Lesson<============================#*


class PayLessonWithCenterCode(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lesson_code = request.data.get("lesson_code")
        student = request.user.student
        

        get_code = get_object_or_404(LessonCode,code=lesson_code,student=None)

        if get_code.student and get_code.available == False:
            raise ValidationError({"detail": "الكود مستخدم من قبل"})
        
        if get_code.lesson.pending:
            raise ValidationError({"detail": "الدرس لسه متفعلش"})

        # Create invoice
        create = Invoice.objects.create(
            student=student,
            lesson=get_code.lesson,
            pay_status="C",
            pay_method="C",
            code = get_code.code,
            price = get_code.price,
            pay_at = timezone.now(),
            expires_at = timezone.now(),
        )

        # Update any existing pending invoices for this student and course to expired
        Invoice.objects.filter(student=student, lesson=get_code.lesson, pay_status='P').update(
            pay_status='E',
            expires_at=timezone.now()
        )
        get_code.student = student
        get_code.available = False
        get_code.save()

        
        return Response(status=status.HTTP_200_OK)


class PayAnyLessonWithCenterCode(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code = request.data.get("code")
        lesson_id = request.data.get("lesson_id")
        student = request.user.student

        get_code = get_object_or_404(AnyLessonCode,code=code)
        get_lesson = get_object_or_404(Lesson,id=lesson_id,unit__course=get_code.course)

        if get_code.student and get_code.available == False and get_code.lesson:
            raise ValidationError({"detail": "الكود مستخدم من قبل"})

        if get_lesson.pending:
            raise ValidationError({"detail": "الدرس لسه متفعلش"})
            
        # Create invoice
        create = Invoice.objects.create(
                student=student,
                lesson=get_lesson,
                pay_status="C",
                pay_method="C",
                code = get_code.code,
                price = get_code.price,
                pay_at = timezone.now(),
                expires_at = timezone.now(),
        )
        get_code.student = student
        get_code.available = False
        get_code.lesson = get_lesson
        get_code.save()
        
        return Response(status=status.HTTP_200_OK)
import random
# DJANGO LIB
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .utils import store_user_activity
from django.utils import timezone
#REST LIB
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.test import APIRequestFactory
from rest_framework import generics
from rest_framework.filters import SearchFilter
# FILES
from .models import *
from .serializers.student_profile import *
from .serializers.student_invoice import *
from .serializers.student_subscription import *
from .serializers.student_view import *
from .serializers.student_notification import *
from .serializers.student_center import *
from .utils import *
# MODELS
from subscription.models import CourseSubscription
from view.models import *
from notification.models import Notification
from desktop_app.models import ResultExamCenter,Attendance


#* < ==============================[ <- Authentication -> ]============================== > ^#
class StudentSignInView(APIView):
    """
    Handle student sign-in requests by validating credentials and returning JWT tokens upon successful authentication.
    """

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate the user with provided credentials
        user = authenticate(username=username, password=password)

        # If authentication is successful, generate and return JWT tokens
        if user is not None:
            refresh = RefreshToken.for_user(user)  # Generate refresh token
            access = AccessToken.for_user(user)    # Generate access token
            
            # Add Header Name To Token
            access_token = f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access}'
            refresh_token = f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {refresh}'
            
            # Store Token In Student Model
            student = user.student
            student.jwt_token = access_token
            student.save()

            # Store user activity
            store_user_activity(request, user)

            return Response({
                'refresh_token':refresh_token,
                'access_token': access_token,
            })

        # If authentication fails, return an error response
        return Response(
            {'error': 'Invalid Credentials'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class StudentSignUpView(APIView):
    """
    Handle student sign-up requests, validate input data, and return an access token upon successful registration.
    """

    def post(self, request):
        # Initialize the serializer with the incoming data
        serializer = StudentSignUpSerializer(data=request.data)

        # Validate the data provided by the user
        if serializer.is_valid():
            # Save the valid data, creating a new student instance
            student = serializer.save()

            # Generate an access token for the associated user
            access_token = AccessToken.for_user(student.user)
            
            # Save access_token in model student
            student.jwt_token = f'Bearer {access_token}'
            student.save()
            
            # Return the access token in the response
            return Response(
                {"access_token": f'{settings.SIMPLE_JWT["AUTH_HEADER_TYPES"]} {access_token}'},
                status=status.HTTP_200_OK
            )

        # If validation fails, return the errors in the response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentSignCodeView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,*args, **kwargs):
        code = request.data.get("code")
        student = request.user.student

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


#* < ==============================[ <- Reset Password  -> ]============================== > ^#

#^ Step 1 
class RequestResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        
        if not username:
            return Response({"detail": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user=User.objects.get(username=username)

        except User.DoesNotExist:
            
            return Response({"error":"the user not found"},status=status.HTTP_404_NOT_FOUND)

        # Generate a 6-digit PIN code
        pin_code = str(random.randint(100000, 999999))

        # Store the PIN code in cache for validation later
        cache.set(username, pin_code, timeout=60)  # 1 minutes validity
        
        # Send the PIN code to the user's WhatsApp number
        req_send = send_whatsapp_massage(
            massage=f'Your PIN code is {pin_code}',
            phone_number=f'{username}'
        )
        return Response({"success":req_send['success']}, status=status.HTTP_200_OK)

#^ Step 2
class VerifyPinCodeView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        pin_code = request.data.get('pin_code')

        if not username or not pin_code:
            return Response({"massage": "Phone number and PIN code are required.","success":False}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the stored PIN code from cache
        stored_pin_code = cache.get(username)

        if stored_pin_code is None:
            return Response({"massage": "PIN code has expired or was not sent.","success":False}, status=status.HTTP_400_BAD_REQUEST)

        if stored_pin_code != pin_code:
            return Response({"massage": "Invalid PIN code.","success":False}, status=status.HTTP_400_BAD_REQUEST)

        # If the PIN code is valid, reset the password or proceed with further actions
        return Response({"massage": "PIN code verified successfully.","success":True}, status=status.HTTP_200_OK)

#^ Step 3
class ResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        pin_code = request.data.get('pin_code')
        new_password = request.data.get('new_password')

        if not username or not pin_code or not new_password:
            return Response({"massage": "Phone number, PIN code, and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Use APIRequestFactory to create a compatible HttpRequest for VerifyPinCodeView
        factory = APIRequestFactory()
        verify_request = factory.post('',data={'username': username, 'pin_code': pin_code})
        

        # Call VerifyPinCodeView
        verify_response = VerifyPinCodeView.as_view()(verify_request)
        if verify_response.status_code != status.HTTP_200_OK:
            return verify_response  # Invalid PIN code

        # Reset the password (assuming User model is used)
        try:
            user = User.objects.get(username=username)  # Adjust this based on your model
        except User.DoesNotExist:
            return Response({"massage": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()
        cache.delete(username)
        return Response({"massage": "Password reset successfully.","success":True}, status=status.HTTP_200_OK)


#* < ==============================[ <- Profile -> ]============================== > ^#

class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        
        student = get_object_or_404(
            Student.objects.select_related('user', 'type_education', 'year'),
            user=request.user
        )
        
        res_data = StudentProfileSerializer(student).data
        
        return Response(res_data, status=status.HTTP_200_OK)


#* < ==============================[ <- Invoice  -> ]============================== > ^#

class StudentInvoiceList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentInvoiceSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]
    filterset_fields = [
        'pay_status',
        'pay_method',
        'free'
        ]
    search_fields = ['sequence']

    def get_queryset(self):
        return Invoice.objects.filter(student=self.request.user.student).order_by("-created")


#* < ==============================[ <- Subscription  -> ]============================== > ^#

class CourseSubscriptionList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListCourseSubscriptionSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]

    def get_queryset(self):
        return CourseSubscription.objects.filter(student=self.request.user.student,active=True).order_by("-created")

class LessonSubscriptionList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListLessonSubscriptionSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter]

    def get_queryset(self):
        return LessonSubscription.objects.filter(student=self.request.user.student,active=True).order_by("-created")

class CourseSubscriptionDetails(generics.RetrieveAPIView):
    serializer_class = ListCourseSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return active subscriptions for the logged-in student."""
        return CourseSubscription.objects.filter(
            student=self.request.user.student,
            active=True
        )

    def get_object(self):
        """Retrieve the subscription by ID."""
        subscription_id = self.kwargs.get("subscription_id")
        return get_object_or_404(self.get_queryset(), id=subscription_id)

#* < ==============================[ <- Views  -> ]============================== > ^#


class ViewsLessonList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentLessonViewList
    filter_backends = [DjangoFilterBackend,SearchFilter]

    search_fields = [
        'lesson__name',
        ]
    filterset_fields = [
            'lesson',
        ]

    def get_queryset(self):
        return LessonView.objects.filter(student=self.request.user.student,counter__gte = 1).order_by("-created")

#* < ==============================[ <- Notifications  -> ]============================== > ^#

class NotificationList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentNotificationSerializer
    filterset_fields = ['is_read',]
    
    def get_queryset(self):
        return Notification.objects.filter(student=self.request.user.student).order_by("is_read","-created_at")
    

#* < ==============================[ <- CENTER -> ]============================== > ^#

class CenterResultExamList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResultExamCenterSerializer

    def get_queryset(self):
        return ResultExamCenter.objects.filter(student=self.request.user.student).order_by("-created")
    

class CenterAttendanceList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceCenterSerializer

    def get_queryset(self):
        return  Attendance.objects.filter(student=self.request.user.student).order_by("-created")
    



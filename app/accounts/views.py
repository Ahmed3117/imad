import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login,logout,authenticate
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password

from subscriptions.models import GroupTime, Lecture, LectureFile, StudyGroup
from .models import TeacherInfo, User, StudentProfile
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.db.models import Q, Sum, Prefetch, F
from courses.models import   Course, CourseTranslation, Level, LevelTranslation, TrackTranslation
from .forms import SessionURLForm
from django.core.mail import send_mail
from django.conf import settings
import random
from django.views.decorators.cache import never_cache

import logging

# Set up logging
logger = logging.getLogger(__name__)

class EmailVerification:
    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))

    @staticmethod
    def send_otp_email(email, otp, purpose="verification"):
        subject = "Email Verification" if purpose == "verification" else "Password Reset"
        message = f"Your OTP for {purpose} is: {otp}"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

def register(request):
    """Render the registration page (Step 1)."""
    return render(request, 'accounts/register.html')

@csrf_exempt
def register_user(request):
    """Handle user registration with email verification."""
    if request.method == 'POST':
        step = request.POST.get('step')

        if step == '1':
            # Handle Step 1: Initial user data collection
            email = request.POST.get('email')
            username = request.POST.get('username')

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already exists'})

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Username already exists'})

            # Generate and send OTP
            otp = EmailVerification.generate_otp()
            request.session['registration_otp'] = otp
            request.session['registration_data'] = request.POST.dict()
            EmailVerification.send_otp_email(email, otp)

            return JsonResponse({'success': True, 'message': 'OTP sent to your email'})

        elif step == 'verify_otp':
            # Handle OTP verification
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('registration_otp')
            registration_data = request.session.get('registration_data')

            if not stored_otp or not registration_data:
                return JsonResponse({'success': False, 'error': 'Session expired'})

            if entered_otp != stored_otp:
                return JsonResponse({'success': False, 'error': 'Invalid OTP'})

            try:
                # Create user after OTP verification
                user = User.objects.create(
                    username=registration_data['username'],
                    email=registration_data['email'],
                    password=make_password(registration_data['password']),
                    name=registration_data['name'],
                    phone=registration_data['phone'],
                    image=request.FILES.get('image'),
                    role=registration_data['role']
                )

                # Clear session data
                del request.session['registration_otp']
                del request.session['registration_data']

                login(request, user)

                # Redirect based on role
                if user.role == 'parent':
                    return JsonResponse({'success': True, 'role': 'parent'})

                return JsonResponse({'success': True, 'role': 'student'})

            except Exception as e:
                logger.error(f"Error creating user: {e}")
                return JsonResponse({'success': False, 'error': 'Error creating user'})

        elif step == '2':
            # Handle Step 2: Profile creation based on role
            user = request.user
            if user.role == 'parent':
                account_type = request.POST.get('account_type')
                parent_profile, created = ParentProfile.objects.update_or_create(
                    user=user,
                    defaults={'type': account_type}
                )
            elif user.role == 'student':
                parent_phone = request.POST.get('parent_phone')
                age = request.POST.get('age')
                StudentProfile.objects.create(user=user, parent_phone=parent_phone, age=age)

            return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

def forgot_password(request):
    """Handle password reset request."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            otp = EmailVerification.generate_otp()
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            EmailVerification.send_otp_email(email, otp, purpose="reset")
            return JsonResponse({'success': True, 'message': 'OTP sent to your email'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Email not found'})
    return render(request, 'accounts/forgot_password.html')

def verify_reset_otp(request):
    """Verify OTP for password reset."""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('reset_otp')
        
        if entered_otp == stored_otp:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid OTP'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def reset_password(request):
    """Reset password after OTP verification."""
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        email = request.session.get('reset_email')
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Session expired'})
        
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        
        # Clear session data
        del request.session['reset_otp']
        del request.session['reset_email']
        
        return JsonResponse({'success': True, 'message': 'Password reset successfully'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def edit_profile(request):
    """Edit user profile."""
    if request.method == 'POST':
        user = request.user
        user.name = request.POST.get('name', user.name)
        user.phone = request.POST.get('phone', user.phone)
        if 'image' in request.FILES:
            user.image = request.FILES['image']
        user.save()

        if user.role == 'parent':
            parent_profile = ParentProfile.objects.get(user=user)
            parent_profile.type = request.POST.get('account_type', parent_profile.type)
            parent_profile.save()
        elif user.role == 'student':
            student_profile = StudentProfile.objects.get(user=user)
            student_profile.age = request.POST.get('age', student_profile.age)
            student_profile.parent_phone = request.POST.get('parent_phone', student_profile.parent_phone)
            student_profile.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('accounts:profile')

    return render(request, 'accounts/edit_profile.html')

# User login view
@never_cache
def user_login(request):
    # Add cache control headers to prevent back button access
    response = HttpResponse()
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    if request.user.is_authenticated:
        # Check the user role and redirect accordingly
        if hasattr(request.user, 'role') and request.user.role == 'parent':
            return redirect('/accounts/parent_dashboard')
        if hasattr(request.user, 'role') and request.user.role == 'teacher':
            return redirect('/a_d_m_i_n/')
        return redirect('/')

    if request.method == 'GET':
        next_url = request.GET.get('next')
        if next_url:
            request.session['next_url'] = next_url
        response = render(request, 'accounts/login.html')
        # Add cache headers to the rendered response
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        # Try to authenticate using the username
        user = authenticate(request, username=identifier, password=password)

        # If authentication fails, try to authenticate using the email
        if user is None:
            try:
                user = User.objects.get(email=identifier)
                user = authenticate(request, username=user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            # Redirect based on role or next URL
            if hasattr(user, 'role') and user.role == 'parent':
                return redirect('/accounts/parent_dashboard')
            if hasattr(request.user, 'role') and request.user.role == 'teacher':
                return redirect('/a_d_m_i_n/')

            next_url = request.session.get('next_url', '/')  # Default to '/' if no next_url
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')

    response = render(request, 'accounts/login.html')
    # Add cache headers to the error response
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@csrf_exempt
def login_student(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        student_username = request.POST.get('student_username')

        user = authenticate(request, username=student_username, password=password)
        if user is not None:
            logout(request)
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid credentials.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})



def profile(request):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    if not request.user.is_authenticated:
        return redirect('accounts:login')

    context = {}

    # Fetch study groups based on user role
    if request.user.role == 'teacher':
        study_groups = StudyGroup.objects.filter(teacher=request.user)
    elif request.user.role == 'student':
        study_groups = StudyGroup.objects.filter(students=request.user)
    else:
        study_groups = StudyGroup.objects.none()  # Empty queryset for non-teacher/student users

    # Handle filtering by course name or teacher name
    search_query = request.GET.get('search', '')
    if search_query:
        study_groups = study_groups.filter(
            Q(course__name__icontains=search_query) |
            Q(teacher__username__icontains=search_query)
        )

    # Fetch translations and group times for study groups
    study_groups_data = []
    for study_group in study_groups:
        # Fetch translation for the course name and description
        course_translation = CourseTranslation.objects.filter(
            course=study_group.course, language=language
        ).first()

        # Fallback to default course name and description if translation is not available
        course_name = course_translation.translated_name if course_translation else study_group.course.name
        course_description = course_translation.translated_description if course_translation else study_group.course.description

        # Fetch group times for this study group
        group_times = GroupTime.objects.filter(group=study_group)

        study_groups_data.append({
            'id': study_group.id,
            'course_name': study_group.course.name,
            'course_description': course_description,
            'course_image': study_group.course.image.url if study_group.course.image else None,
            'teacher': study_group.teacher.name,
            'students': study_group.students.all(),
            'capacity': study_group.capacity,
            'number_of_expected_lectures': study_group.number_of_expected_lectures,
            'join_price': study_group.join_price,
            'group_times': group_times,
        })

    context = {
        'study_groups': study_groups_data,
        'user_role': request.user.role,
        'search_query': search_query,
    }

    return render(request, 'accounts/profile.html', context)


# Parent Dashboard
def parent_dashboard(request):
    if request.user.role != 'parent':
        return HttpResponse("Unauthorized", status=403)
    
    parent_profile = get_object_or_404(ParentProfile, user=request.user)
    parent_students = ParentStudent.objects.filter(parent=request.user)
    print(parent_students)
    return render(request, 'accounts/parent_dashboard.html', {'parent_students': parent_students})

# User Logout
def user_logout(request):
    logout(request)
    return redirect('accounts:login')


# Add Student under Parent
@csrf_exempt
def add_student(request):
    if request.method == 'POST' and request.user.role == 'parent':
        student_name = request.POST.get('name')
        student_username = request.POST.get('username')
        student_password = request.POST.get('password')
        student_age = request.POST.get('age')
        profile_image = request.FILES.get('profile_image')

        # Create student user
        student_user = User.objects.create(
            username=student_username,
            password=make_password(student_password),
            name=student_name,
            image=profile_image,
            role='student'
        )
        print(student_user)
        # Get the parent's phone number
        parent_phone = request.user.phone

        # Create student profile
        StudentProfile.objects.create(user=student_user, age=student_age, parent_phone=parent_phone)

        # Link parent and student
        ParentStudent.objects.create(parent=request.user, student=student_user)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Unauthorized request'})


def study_group_lectures(request, study_group_id):
    # Fetch the StudyGroup object or return a 404 if not found
    study_group = get_object_or_404(StudyGroup, id=study_group_id)
    
    # Fetch all lectures associated with the study group
    lectures = Lecture.objects.filter(group=study_group)
    
    # For each lecture, fetch the associated files
    lectures_with_files = []
    for lecture in lectures:
        files = LectureFile.objects.filter(lecture=lecture)
        lectures_with_files.append({
            'lecture': lecture,
            'files': files
        })
    
    # Render the data in the template
    return render(request, 'accounts/lectures.html', {
        'study_group': study_group,
        'lectures_with_files': lectures_with_files
    })






































@login_required
def session_details(request, course_id, student_username):
    # Fetch the subscription for the specific student and course
    student = get_object_or_404(User, username=student_username)
    subscription = Subscription.objects.filter(student=student, course_id=course_id).first()
    if not subscription:
        return redirect('accounts:profile')

    # Get all SubscriptionSession objects related to the student's subscription
    course_sessions = SubscriptionSession.objects.filter(subscription=subscription).select_related('session')

    # Preprocess exams and results for each session
    sessions_data = []
    for session_data in course_sessions:
        session = session_data.session
        exam = Exam.objects.filter(session=session).first()
        exam_result = None
        if exam:
            exam_result = ExamResult.objects.filter(student=request.user, exam=exam).first()
        
        sessions_data.append({
            'session_data': session_data,
            'exam': exam,
            'exam_result': exam_result
        })

    # Handle session creation/update for teachers
    next_session = None
    if request.user.role == 'teacher':
        # Find the next session in order that hasn't been added to the subscription
        completed_session_ids = subscription.completed_sessions.values_list('id', flat=True)
        next_session = Session.objects.filter(course=subscription.course).exclude(id__in=completed_session_ids).order_by('order').first()

        if request.method == 'POST':
            form = SessionURLForm(request.POST)
            if form.is_valid() and next_session:
                # Update or create the SubscriptionSession
                subscription_session, created = SubscriptionSession.objects.get_or_create(
                    session=next_session,
                    subscription=subscription,
                    defaults={
                        'session_url': form.cleaned_data['session_url'],
                        'is_completed': False
                    }
                )
                if not created:
                    # If the SubscriptionSession already exists, update it
                    subscription_session.session_url = form.cleaned_data['session_url']
                    subscription_session.save()
                return redirect('accounts:session_details', course_id=course_id, student_username=student_username)
        else:
            form = SessionURLForm()

    context = {
        'subscription': subscription,
        'sessions_data': sessions_data,
        'next_session': next_session,
        'form': form if request.user.role == 'teacher' else None,
    }
    return render(request, 'accounts/session_details.html', context)


@login_required
def mark_session_completed(request, session_id):
    session = get_object_or_404(SubscriptionSession, id=session_id)
    session.is_completed = True
    session.save()
    session.subscription.completed_sessions.add(session.session)
    return redirect(request.META.get('HTTP_REFERER', 'accounts:session_details'))

@login_required
def start_exam(request, exam_id):
    # Fetch the exam and ensure it belongs to a session the student is subscribed to
    exam = get_object_or_404(Exam, id=exam_id)
    course_id = exam.session.course.id
    # Check if the student has already taken the exam
    exam_result = ExamResult.objects.filter(student=request.user, exam=exam).first()

    # Render the exam page
    return render(request, 'accounts/exam.html', {
        'exam': exam,
        'questions': exam.question_set.all(),
        'exam_result': exam_result,
        'course_id': course_id,
    })

# @csrf_exempt
@login_required
def submit_exam(request, exam_id):
    if request.method == 'POST':
        exam = get_object_or_404(Exam, id=exam_id)
        student = request.user

        # Check if the student has already taken the exam
        existing_result = ExamResult.objects.filter(student=student, exam=exam).first()
        if existing_result:
            return JsonResponse({'status': 'error', 'message': 'Exam already taken'}, status=400)

        data = request.POST

        questions = Question.objects.filter(exam=exam)
        score = 0
        total_questions = questions.count()

        # Calculate score
        for question in questions:
            question_key = f'question_{question.id}'
            selected_option_id = data.get(question_key)
            print(selected_option_id)
            if selected_option_id:
                try:
                    selected_option = Option.objects.get(
                        id=selected_option_id,
                        question=question  # Ensure the option belongs to this question
                    )
                    if selected_option.is_correct:
                        score += 1
                except Option.DoesNotExist:
                    continue

        # Calculate percentage score
        final_score = round((score / total_questions) * 100, 2)

        # Save the exam result
        ExamResult.objects.create(
            student=student,
            exam=exam,
            score=final_score,
            is_completed=True
        )

        return JsonResponse({
            'status': 'success',
            'score': final_score,
            'correct_answers': score,
            'total_questions': total_questions
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

import json

def get_available_slots(request):
    day = request.GET.get('day')
    subscription_id = request.GET.get('subscription_id')
    
    # Get the subscription and its course
    subscription = get_object_or_404(Subscription, id=subscription_id)
    course = subscription.course
    print(course)
    # Get all teachers who teach the course
    teachers = TeacherInfo.objects.filter(courses=course).values_list('teacher', flat=True)
    print(teachers)
    # Get all availability slots for these teachers on the selected day
    available_slots = TeacherAvailability.objects.filter(
        day=day,
        teacher__in=teachers,
        is_available=True
    )
    print(available_slots)
    # Prepare the available times
    available_times = []
    for slot in available_slots:
        available_times.append({
            'start': slot.start_time.strftime('%H:%M'),
            'end': slot.end_time.strftime('%H:%M')
        })
    
    # Remove duplicates while preserving order
    unique_available_times = []
    for time in available_times:
        if time not in unique_available_times:
            unique_available_times.append(time)
    
    return JsonResponse({'available_times': unique_available_times})

@csrf_exempt  
@require_POST
def create_appointment(request):
    try:
        # Parse JSON data from the request
        data = json.loads(request.body)
        subscription_id = data.get('subscription_id')
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # Validate input
        if not all([subscription_id, day, start_time, end_time]):
            return JsonResponse({
                'success': False, 
                'error': 'Missing required fields'
            }, status=400)

        # Get the subscription and course
        subscription = Subscription.objects.get(id=subscription_id)
        course = subscription.course

        # Get the teacher IDs who teach the course
        teacher_ids = TeacherInfo.objects.filter(courses=course).values_list('teacher_id', flat=True)

        # Find an available teacher
        available_teacher = (
            TeacherAvailability.objects.filter(
                day=day,
                start_time=start_time,
                end_time=end_time,
                is_available=True,
                teacher_id__in=teacher_ids
            )
            .first()
        )

        if not available_teacher:
            return JsonResponse({
                'success': False, 
                'error': 'No available teacher found'
            }, status=400)

        # Create the Appointment
        appointment = Appointment.objects.filter(subscription=subscription).first()
        if appointment:
            return JsonResponse({
                'success': True,
                'appointment_id': appointment.id,
                'message': 'this subscription already has a scuedual.'
            })

        appointment = Appointment.objects.create(
            subscription=subscription,
            avialability=available_teacher,
            is_active=True,
        )

        # Update the teacher's availability
        available_teacher.is_available = False
        available_teacher.save()

        return JsonResponse({
            'success': True,
            'appointment_id': appointment.id,
            'message': 'Appointment successfully created'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid JSON'
        }, status=400)
    except Subscription.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid subscription ID'
        }, status=404)
    except Exception as e:
        print(f"Error creating appointment: {str(e)}")  # For debugging
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)









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
from courses.models import   Course, CourseTranslation, Level, LevelTranslation, Track, TrackTranslation
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
            if user.role == 'student':
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
        if hasattr(request.user, 'role') and request.user.role == 'teacher':
            return redirect('/accounts/profile')
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
            if hasattr(request.user, 'role') and request.user.role == 'teacher':
                return redirect('/accounts/profile')

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

    # Fetch study groups based on user role
    if request.user.role == 'teacher':
        study_groups = StudyGroup.objects.filter(teacher=request.user)
    elif request.user.role == 'student':
        study_groups = StudyGroup.objects.filter(students=request.user)
    else:
        study_groups = StudyGroup.objects.none()  # Empty queryset for non-teacher/student users

    # Get filter and search parameters from GET request
    search_query = request.GET.get('search', '')
    course_id = request.GET.get('course', '')
    level_id = request.GET.get('level', '')
    track_id = request.GET.get('track', '')
    day = request.GET.get('day', '')

    # Apply filters
    if search_query:
        study_groups = study_groups.filter(
            Q(course__name__icontains=search_query) |
            Q(teacher__username__icontains=search_query)
        )
    if course_id:
        study_groups = study_groups.filter(course__id=course_id)
    if level_id:
        study_groups = study_groups.filter(course__level__id=level_id)
    if track_id:
        study_groups = study_groups.filter(course__track__id=track_id)
    if day:
        study_groups = study_groups.filter(group_times__day=day)

    # Fetch all courses, levels, tracks, and days for filter dropdowns (only for teachers)
    courses = Course.objects.all() if request.user.role == 'teacher' else []
    levels = Level.objects.all() if request.user.role == 'teacher' else []
    tracks = Track.objects.all() if request.user.role == 'teacher' else []
    days = GroupTime.DAY_CHOICES  # Use the DAY_CHOICES from the GroupTime model

    # Prepare study groups data
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
            'course_name': course_name,
            'course_description': course_description,
            'course_image': study_group.course.image.url if study_group.course.image else None,
            'teacher': study_group.teacher.username,
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
        'courses': courses,
        'levels': levels,
        'tracks': tracks,
        'days': days,
        'selected_course': course_id,
        'selected_level': level_id,
        'selected_track': track_id,
        'selected_day': day,
    }

    return render(request, 'accounts/profile.html', context)



# User Logout
def user_logout(request):
    logout(request)
    return redirect('accounts:login')




from django.utils import timezone
from django.contrib import messages
import requests
from django import forms
# Forms
class LectureForm(forms.ModelForm):
    SCHEDULE_CHOICES = [
        ('NOW', 'Now'),
    ]
    schedule = forms.ChoiceField(choices=SCHEDULE_CHOICES, label="Schedule", required=True)

    class Meta:
        model = Lecture
        fields = ['title', 'description', 'duration']

    def __init__(self, *args, **kwargs):
        study_group = kwargs.pop('study_group', None)
        super().__init__(*args, **kwargs)
        if study_group:
            group_times = [(str(gt.id), str(gt)) for gt in GroupTime.objects.filter(group=study_group)]
            self.fields['schedule'].choices = self.SCHEDULE_CHOICES + group_times

    def clean(self):
        cleaned_data = super().clean()
        schedule = cleaned_data.get('schedule')
        if not schedule:
            raise forms.ValidationError("Schedule is required.")
        return cleaned_data


class LectureFileForm(forms.ModelForm):
    class Meta:
        model = LectureFile
        fields = ['file']

# Helper function to check access
def check_study_group_access(request, study_group):
    if request.user.role == 'teacher' and study_group.teacher != request.user:
        return False
    elif request.user.role == 'student' and request.user not in study_group.students.all():
        return False
    return True

# Helper function to create Zoom meeting
def create_zoom_meeting(title, description, duration, date, time, timezone='Africa/Cairo'):
    zoom_data = {
        'topic': title,
        'agenda': description,
        'duration': duration,
        'date': date.strftime('%Y-%m-%d'),
        'time': time.strftime('%H:%M'),
        'timezone': timezone,
    }
    try:
        response = requests.post(
            'http://127.0.0.1:8800/subscriptions/create-meeting/',
            data=zoom_data
        )
        if response.status_code == 200:
            return response.json().get('meeting_url')
        return None
    except Exception as e:
        print(f"Error creating Zoom meeting: {str(e)}")
        return None

# Main view to display lectures
@login_required
def study_group_lectures(request, study_group_id):
    study_group = get_object_or_404(StudyGroup, id=study_group_id)
    if not check_study_group_access(request, study_group):
        return render(request, '403.html', status=403)

    lectures = Lecture.objects.filter(group=study_group)
    lectures_with_files = [
        {'lecture': lecture, 'files': LectureFile.objects.filter(lecture=lecture)}
        for lecture in lectures
    ]

    lecture_form = LectureForm(study_group=study_group) if request.user.role == 'teacher' else None
    file_form = LectureFileForm() if request.user.role == 'teacher' else None

    return render(request, 'accounts/lectures.html', {
        'study_group': study_group,
        'lectures_with_files': lectures_with_files,
        'lecture_form': lecture_form,
        'file_form': file_form,
        'user_role': request.user.role,
    })

# Add a new lecture
@login_required
def add_lecture(request, study_group_id):
    study_group = get_object_or_404(StudyGroup, id=study_group_id)
    if request.user.role != 'teacher' or study_group.teacher != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        form = LectureForm(request.POST, study_group=study_group)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.group = study_group
            lecture.save()

            schedule = form.cleaned_data['schedule']
            if schedule == 'NOW':
                live_link = create_zoom_meeting(
                    lecture.title, lecture.description, lecture.duration,
                    timezone.now(), timezone.now()
                )
            else:
                group_time = GroupTime.objects.get(id=int(schedule))
                live_link = create_zoom_meeting(
                    lecture.title, lecture.description, lecture.duration,
                    timezone.now(), group_time.time  # Assuming current date for simplicity
                )

            if live_link:
                lecture.live_link = live_link
                lecture.live_link_date = timezone.now()
                lecture.save()
                return JsonResponse({'success': True, 'message': 'Lecture added successfully'})
            return JsonResponse({'success': False, 'message': 'Failed to create Zoom meeting'})
        return JsonResponse({'success': False, 'message': 'Invalid form data: ' + str(form.errors)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

# Update an existing lecture
import logging

logger = logging.getLogger(__name__)

@login_required
def update_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    if request.user.role != 'teacher' or lecture.group.teacher != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        # Log the incoming POST data for debugging
        logger.info(f"Received POST data for lecture {lecture_id}: {request.POST}")

        # Try full form validation (optional, for reference)
        form = LectureForm(request.POST, study_group=lecture.group, instance=lecture)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Lecture updated successfully'})
        
        # Simplified partial update
        updated = False
        if 'title' in request.POST and request.POST['title'].strip():
            lecture.title = request.POST['title']
            updated = True
        if 'description' in request.POST:
            lecture.description = request.POST['description']
            updated = True
        
        if updated:
            lecture.save()
            return JsonResponse({'success': True, 'message': 'Lecture updated successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'No valid fields provided to update'})

        # Log form errors if we reach here (shouldn’t with the above logic)
        return JsonResponse({'success': False, 'message': f'Invalid form data: {str(form.errors)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

# Reschedule a lecture to "now"
@login_required
def reschedule_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    if request.user.role != 'teacher' or lecture.group.teacher != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        live_link = create_zoom_meeting(
            lecture.title, lecture.description, lecture.duration,
            timezone.now(), timezone.now()
        )
        if live_link:
            lecture.live_link = live_link
            lecture.live_link_date = timezone.now()
            lecture.save()
            return JsonResponse({'success': True, 'message': 'Lecture rescheduled successfully', 'live_link': live_link})
        return JsonResponse({'success': False, 'message': 'Failed to reschedule Zoom meeting'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

# Delete a lecture
@login_required
def delete_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    if request.user.role != 'teacher' or lecture.group.teacher != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        lecture.delete()
        return JsonResponse({'success': True, 'message': 'Lecture deleted successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

# Add files to a lecture
@login_required
def add_lecture_files(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    if request.user.role != 'teacher' or lecture.group.teacher != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        files = request.FILES.getlist('file')
        uploaded_files = []
        for file in files:
            lecture_file = LectureFile(lecture=lecture, file=file)
            lecture_file.save()
            uploaded_files.append({
                'name': lecture_file.file.name.split('/')[-1],
                'url': lecture_file.file.url,
                'size': lecture_file.file.size,
            })
        return JsonResponse({
            'success': True,
            'message': 'Files uploaded successfully',
            'files': uploaded_files
        })
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

# Delete a file
@login_required
def delete_lecture_file(request, file_id):
    lecture_file = get_object_or_404(LectureFile, id=file_id)
    if request.user.role != 'teacher' or lecture_file.lecture.group.teacher != request.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        lecture_file.delete()
        return JsonResponse({'success': True, 'message': 'File deleted successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
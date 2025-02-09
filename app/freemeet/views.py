from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import FreeMeet
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib import messages
from urllib.parse import quote, urlencode
from django.conf import settings
import traceback

@csrf_exempt
@login_required
def request_free_meet(request):
    if request.method == 'POST':
        try:
            student = request.user
            phone_number = student.get_user_phone()
            print(phone_number)
            email = student.get_user_email()

            # Check if the user has already requested a meet
            existing_request = FreeMeet.objects.filter(student=student).first()
            if existing_request:
                return JsonResponse({'status': 'error', 'message': f'You have already requested a meet. Status: {existing_request.respond_status}', 'freemeet': {'respond_status': existing_request.respond_status, 'meet_url': existing_request.meet_url}})

            # Create a new meeting request
            FreeMeet.objects.create(student=student, phone_number=phone_number)
            return JsonResponse({'status': 'success', 'message': 'Your request for a free meet has been submitted successfully.'})
        except Exception as e:
            # Log the error for debugging
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': 'An error occurred while processing your request.'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)






def send_whatsapp(request, freemeet_id):
    """
    Redirect to WhatsApp with the meet URL and phone number for the specified FreeMeet object.
    """
    free_meet = get_object_or_404(FreeMeet, pk=freemeet_id)
    if free_meet.meet_url and free_meet.phone_number:
        message = f"Join the meeting using this link: {free_meet.meet_url}"
        encoded_message = urlencode({'text': message})
        whatsapp_url = f"https://wa.me/{free_meet.phone_number}?{encoded_message}"
        # Update the status to 'scheduled' 
        free_meet.respond_status = 'scheduled'
        free_meet.save()
        return HttpResponseRedirect(whatsapp_url)
    else:
        messages.error(request, "Invalid meet URL or phone number.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def send_meeting_email(request, freemeet_id):
    """
    Send the meeting URL to the student's email.
    """
    free_meet = get_object_or_404(FreeMeet, pk=freemeet_id)
    if free_meet.meet_url and free_meet.student_email:
        subject = "Your Meeting URL"
        message = f"Hello {free_meet.student.get_first_name()},\n\nJoin the meeting using this link: {free_meet.meet_url}\n\nBest regards,\nPlatrainCloud Team"
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,  # Sender
                [free_meet.student_email],  # Recipient
                fail_silently=False,
            )
            # Update the status to 'scheduled'
            free_meet.respond_status = 'scheduled'
            free_meet.save()
            messages.success(request, f"Meeting URL sent to {free_meet.student_email}.")
        except Exception as e:
            messages.error(request, f"Failed to send email: {e}")
    else:
        messages.error(request, "Invalid meet URL or email.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

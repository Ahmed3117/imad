import json
import base64
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
import pytz
import logging
import re
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from accounts.models import TeacheroomAccount

# ACCOUNT_ID = settings.ACCOUNT_ID
# CLIENT_ID = settings.CLIENT_ID
# CLIENT_SECRET = settings.CLIENT_SECRET
TOKEN_URL = settings.TOKEN_URL
MEETING_URL = settings.MEETING_URL



logger = logging.getLogger(__name__)

def get_access_token(client_id, client_secret, account_id):
    auth = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "account_credentials", "account_id": account_id}
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Error fetching access token: {response.text}")

def validate_inputs(topic, agenda, duration, date_str, time_str, timezone):
    errors = []
    if not topic or len(topic) > 200:
        errors.append("Topic is required and cannot exceed 200 characters.")
    if not agenda or len(agenda) > 500:
        errors.append("Agenda is required and cannot exceed 500 characters.")
    if not duration or not duration.isdigit() or int(duration) < 10 or int(duration) > 1440:
        errors.append("Duration must be a number between 10 minutes and 1440 minutes (24 hours).")
    if not date_str or not re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        errors.append("Date must be in YYYY-MM-DD format.")
    if not time_str or not re.match(r"\d{2}:\d{2}", time_str):
        errors.append("Time must be in HH:MM (24-hour) format.")
    if timezone not in pytz.all_timezones:
        errors.append("Invalid timezone provided.")
    return errors

@csrf_exempt
def create_zoom_meeting(request):
    print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        client_id = request.POST.get('client_id')
        client_secret = request.POST.get('client_secret')
        account_id = request.POST.get('account_id')
        topic = request.POST.get('topic')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        duration = request.POST.get('duration')
        agenda = request.POST.get('agenda')
        timezone = "Africa/Cairo"

        errors = validate_inputs(topic, agenda, duration, date_str, time_str, timezone)
        if errors:
            return JsonResponse({'errors': errors}, status=400)

        local_timezone = pytz.timezone(timezone)
        local_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_datetime = local_timezone.localize(local_datetime)
        utc_datetime = local_datetime.astimezone(pytz.utc)

        meeting_data = {
            "topic": topic,
            "agenda": agenda,
            "type": 2,
            "start_time": utc_datetime.isoformat(),
            "duration": int(duration),
            "timezone": timezone,
            "settings": {
                "host_video": True,
                "participant_video": False,
                "audio": "voip",
                "auto_recording": "cloud",
                "waiting_room": False,
                "join_before_host": True,
                "mute_upon_entry": False,
                "approval_type": 2,
                "closed_caption": True,
                "registrants_email_notification": True
            },
        }

        access_token = get_access_token(
            client_id,
            client_secret,
            account_id
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(MEETING_URL, headers=headers, data=json.dumps(meeting_data))

        if response.status_code == 201:
            meeting_info = response.json()
            return JsonResponse({
                'meeting_url': meeting_info['join_url'],
                'start_time': meeting_info['start_time'],
                'agenda': meeting_info['agenda'],
                'password': meeting_info['password']
            })
        elif response.status_code == 400:
            error_message = response.json().get('message', 'Bad Request')
            return JsonResponse({'error': error_message}, status=400)
        elif response.status_code == 404:
            return JsonResponse({'error': 'User does not exist.'}, status=404)
        elif response.status_code == 429:
            return JsonResponse({'error': 'Too many requests, please try again later.'}, status=429)
        else:
            return JsonResponse({'error': 'An unexpected error occurred.'}, status=response.status_code)

    except Exception as e:
        logger.error(f"Error creating meeting: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

def get_meeting_status(request, meeting_id):
    try:
        teacher_zoom_account = TeacheroomAccount.objects.get(user=request.user)
        access_token = get_access_token(
            teacher_zoom_account.client_id,
            teacher_zoom_account.client_secret,
            teacher_zoom_account.account_id
        )
    except TeacheroomAccount.DoesNotExist:
        return JsonResponse({"error": "Teacher Zoom account not found"}, status=404)

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        status = data.get("status", "unknown")
        return JsonResponse({"status": status})

    return JsonResponse({"error": "Meeting not found"}, status=404)

def get_meeting_participants(meeting_id):
    try:
        teacher_zoom_account = TeacheroomAccount.objects.get(user=request.user)
        access_token = get_access_token(
            teacher_zoom_account.client_id,
            teacher_zoom_account.client_secret,
            teacher_zoom_account.account_id
        )
    except TeacheroomAccount.DoesNotExist:
        raise Exception("Teacher Zoom account not found")

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/participants"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("participants", [])
    else:
        raise Exception(f"Error fetching participants: {response.text}")





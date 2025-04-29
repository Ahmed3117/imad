from django.http import JsonResponse
from django.conf import settings
from google.oauth2 import service_account
from google.apps import meet_v2 as meet
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.apps import meet_v2 as meet
import os

# If modifying these SCOPES, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/meetings.space.created']

@csrf_exempt
def create_zoom_meeting(request):
    if request.method == 'POST':
        try:
            creds = None

            # Path to token.json and credentials.json
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # adjust as needed
            token_path = os.path.join(BASE_DIR, 'token.json')
            credentials_path = os.path.join(BASE_DIR, 'credentials.json')

            # Check if token.json exists
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # If no valid credentials, ask the user to login
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(token_path, 'w') as token_file:
                    token_file.write(creds.to_json())

            # Now use the credentials to create the Google Meet
            client = meet.SpacesServiceClient(credentials=creds)

            space_obj = meet.Space(
                config=meet.SpaceConfig(access_type=meet.SpaceConfig.AccessType.OPEN)
            )

            meet_request = meet.CreateSpaceRequest(space=space_obj)
            response = client.create_space(request=meet_request)

            # Return the meeting link
            meeting_uri = response.meeting_uri
            return JsonResponse({'meeting_url': meeting_uri})

        except Exception as e:
            print(f"Error creating meeting: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

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





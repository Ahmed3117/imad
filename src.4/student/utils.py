import json
import requests
from django.conf import settings
from student.models import UserActivity
from django.utils import timezone
import user_agents
import requests

def send_whatsapp_massage(phone_number, massage):
    url = "https://whats.easytech-sotfware.com/api/v1/send-text"

    params = {
            "token": settings.WHATSAPP_TOKEN,
            "instance_id": settings.WHATSAPP_ID,
            "msg": massage,
            "jid": f"2{phone_number}@s.whatsapp.net"
        }
    
    req = requests.get(url, params=params)
    
    return req.json()


def store_user_activity(request, user):
    """
    Store user activity information including device, browser and OS details
    """
    # Parse user agent string
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    
    # Handle Postman specifically
    if 'PostmanRuntime' in user_agent_string:
        device_name = 'Postman'
        os_name = 'API Testing Tool'
        browser_name = 'Postman'
    else:
        # Parse regular browser/device user agents
        user_agent = user_agents.parse(user_agent_string)
        device_name = user_agent.device.family
        os_name = user_agent.os.family
        browser_name = user_agent.browser.family

    UserActivity.objects.create(
        user=user,
        device_name=device_name,
        os_name=os_name,
        browser_name=browser_name,
        last_active=timezone.now(),
        login_time=timezone.now()
    )


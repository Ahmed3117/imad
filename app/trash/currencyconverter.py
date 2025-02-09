# views.py
from django.http import JsonResponse
import requests

def convert_usd_to_egp(request, amount):
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        conversion_rate = data["rates"]["EGP"]
        converted_amount = amount * conversion_rate
        round(converted_amount, 2)
    else:
        // try again for 5 times and if it fails return error
        

import uuid
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render,redirect

from courses.models import Course, Level, Track
from subscriptions.models import Subscription
from orders.models import Order
from .paymob import process_payment, calculate_hmac
# from .utils import process_payment, calculate_hmac
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from django.contrib import messages
import requests
from decimal import Decimal, ROUND_HALF_UP
logger = logging.getLogger(__name__)

def convert_usd_to_egp(request, amount):
    if getattr(request, 'is_egypt', False):
        return amount

    attempts = 0
    max_attempts = 5

    while attempts < max_attempts:
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            conversion_rate = Decimal(str(data["rates"]["EGP"]))  # Convert the rate to Decimal
            converted_amount = (Decimal(str(amount)) * conversion_rate).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )
            return converted_amount

        except requests.exceptions.RequestException as e:
            attempts += 1
            if attempts >= max_attempts:
                raise Exception(f"Failed to convert currency after {max_attempts} attempts: {str(e)}")
        except KeyError as e:
            attempts += 1
            if attempts >= max_attempts:
                raise Exception(f"Failed to parse conversion rate after {max_attempts} attempts: {str(e)}")
        except Exception as e:
            attempts += 1
            if attempts >= max_attempts:
                raise Exception(f"Unexpected error during currency conversion: {str(e)}")


def split_name(full_name):
    prefixes = {"abd", "el", "al"}
    parts = full_name.split()
    
    if len(parts) == 1:
        return full_name, full_name  
    
    first_name = parts[0]
    last_name = " ".join(parts[1:]) 

    if len(parts) > 1 and any(parts[1].lower().startswith(prefix) for prefix in prefixes):
        first_name = " ".join(parts[:2])
        last_name = " ".join(parts[2:])

    if not last_name.strip():
        last_name = first_name

    return first_name, last_name

def payment_view(request, order_id=None):
    order = None
    try:
        order = get_object_or_404(Order, order_id=order_id)
        if order.status == 'done':
            messages.error(request, 'This order has already been completed.')
            return render(request, "payment.html")

    except Order.DoesNotExist:
        messages.error(request, 'This order is not valid.')
        return render(request, "payment.html")

    if request.method == "GET":
        context = {
            "order": order,
            "total_price": convert_usd_to_egp(request, order.calculate_total_price()),
        }
        return render(request, "payment.html", context)

    elif request.method == "POST":
        try:
            # Collect data from the form
            payment_method = request.POST.get("payment_method", "card").strip().lower()
            amount_cents = convert_usd_to_egp(request, order.calculate_total_price()) * 100
            currency = "EGP"

            print("------------------")
            print(order.student.get_user_email())

            first_name, last_name = split_name(order.student.name or 'none')
            billing_data = {
                "name": order.student.name,
                "email": order.student.get_user_email() or 'none@gmail.com',
                "phone_number": order.student.get_user_phone() or '00000000000',
                "first_name": first_name,
                "last_name": last_name,
                "apartment": request.POST.get("apartment", "none"),
                "floor": request.POST.get("floor", "none"),
                "street": request.POST.get("street", "none"),
                "building": request.POST.get("building", "none"),
                "city": request.POST.get("city", "none"),
                "country": request.POST.get("country", "EG"),
                "state": request.POST.get("state", "none"),
            }

            merchant_order_id = order_id
            order_items = []

            # Validate required fields
            if not payment_method or not amount_cents:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            checkout_url = process_payment(payment_method, merchant_order_id, amount_cents, currency, billing_data, order_items)
            print(checkout_url)
            return JsonResponse({"checkout_url": checkout_url}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def payment_callback(request):
    if request.method == 'GET':
        print("I am in GET request now")
        print(request)

        query_string = request.GET
        success_value = query_string.get('success')

        print(f"Success Value: {success_value}")
        if success_value:
            order_id = query_string.get('merchant_order_id').split('#')[0]
            order = get_object_or_404(Order, order_id=order_id)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print(order_id) 
            # Add the order levels, tracks, and courses to the student's subscriptions
            order = get_object_or_404(Order, order_id=order_id)
            for item in order.items.all():
                if isinstance(item.content_object, Course):
                    Subscription.objects.create(student=order.student, course=item.content_object, status='active')
                elif isinstance(item.content_object, Track):
                    for course in item.content_object.courses.all():
                        Subscription.objects.create(student=order.student, course=course, status='active')
                elif isinstance(item.content_object, Level):
                    for course in item.content_object.courses.filter(track__isnull=True):
                        Subscription.objects.create(student=order.student, course=course, status='active')
                    for track in item.content_object.tracks.all():
                        for course in track.courses.all():
                            Subscription.objects.create(student=order.student, course=course, status='active')
            # Update the order status to 'done'
            print(f'order: {order}') 
            order.status = 'done'
            print(f'order status: {order.status}')
            order.save()
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

            # Calculating HMAC
            textType = "request"
            calculated_hmac = calculate_hmac(query_string, textType)
            print(f"Calculated HMAC: {calculated_hmac}")

            # Checking HMAC validity
            hmac_received = query_string.get('hmac', None)
            print(f"Received HMAC: {hmac_received}")

            if hmac_received == calculated_hmac:
                return redirect('/accounts/profile/')
            else:
                return render(request, "failed.html")

    elif request.method == 'POST':
        print("I am in POST request now")
        print(request)
        payload = json.loads(request.body)
        print(f"Received POST payload: {payload}")
        try:
            hmac_received = request.GET.get('hmac')

            # Step 3: Calculate the HMAC
            textType = "payload"
            calculated_hmac = calculate_hmac(payload, textType)
            print(f"Calculated HMAC: {calculated_hmac}")
            print(f"Received HMAC: {hmac_received}")

            # Compare HMACs
            if hmac_received != calculated_hmac:
                print(f"HMAC mismatch! Received: {hmac_received}, Calculated: {calculated_hmac}")
                return JsonResponse({"error": "Invalid HMAC signature"}, status=400)

            # Step 4: Process the callback response
            transaction_status = payload.get("obj", {}).get("success")
            print(transaction_status)
            order_id = payload.get("order", {}).get("id")
            amount_cents = payload.get("amount_cents")
            error_message = payload.get("error_message")

            if transaction_status:
                request.session['is_payment_successful'] = True
                print(f"Payment successful: Order ID {order_id}")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                return JsonResponse({"message": "Payment success"}, status=200)
            else:
                print(f"Payment failed: {error_message}")
                return JsonResponse({"message": "Payment failed", "error": error_message}, status=400)

        except Exception as e:
            print(f"Error processing callback: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


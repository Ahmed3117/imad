import os
import ast
import requests
from dotenv import load_dotenv
import os
import json
import requests
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
HMAC_KEY = os.getenv("HMAC_KEY")
raw_payment_methods = os.getenv("PAYMENT_METHODS", "{}")
raw_payment_methods_cleaned = raw_payment_methods.replace("\u00A0", "").strip()
# Print the values to verify
print("raw_payment_methods:", raw_payment_methods)
print("API_KEY:", API_KEY)
print("HMAC_KEY:", HMAC_KEY)

try:
    PAYMENT_METHODS = ast.literal_eval(raw_payment_methods_cleaned)
    print("PAYMENT_METHODS:", PAYMENT_METHODS)
except (SyntaxError, ValueError) as e:
    print("Failed to parse PAYMENT_METHODS:", e)
    PAYMENT_METHODS = {}

BASE_URL = "https://accept.paymobsolutions.com/api"
IFRAME_BASE_URL = "https://accept.paymobsolutions.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_token}"


def get_auth_token():
    """Get the authentication token using API Key."""
    auth_url = f"{BASE_URL}/auth/tokens"
    response = requests.post(auth_url, json={"api_key": API_KEY})
    if response.status_code == 201:
        return response.json().get("token")
    else:
        raise Exception(f"Error getting auth token: {response.json()}")

def register_order(auth_token, order_info):
    """Register an order or fetch existing order ID if already created."""
    order_url = f"{BASE_URL}/ecommerce/orders"
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Check if the order already exists
    existing_order_url = f"{order_url}?merchant_order_id={order_info['merchant_order_id']}"
    existing_order_response = requests.get(existing_order_url, headers=headers)

    if existing_order_response.status_code == 200:
        response_data = existing_order_response.json()
        results = response_data.get("results", [])  # Get the results list
        if results:
            existing_order_id = results[0]['id']  # Extract the first order ID
            print(f"Found existing order: {existing_order_id}")
            return existing_order_id

    # If no existing order, create a new one
    response = requests.post(order_url, json=order_info, headers=headers)
    if response.status_code == 201:
        return response.json().get("id")
    else:
        raise Exception(f"Error registering order: {response.json()}")

def get_payment_token(auth_token, order_id, billing_data, payment_method, amount_cents, currency):
    """Generate a new payment token for the same order."""
    if payment_method not in PAYMENT_METHODS:
        raise Exception(f"Payment method '{payment_method}' is not supported.")
    
    iframe_id = PAYMENT_METHODS[payment_method]["iframe_id"]
    integration_id = PAYMENT_METHODS[payment_method]["integration_id"]

    payment_url = f"{BASE_URL}/acceptance/payment_keys"
    headers = {"Authorization": f"Bearer {auth_token}"}

    payment_data = {
        "auth_token": auth_token,
        "order_id": order_id,
        "integration_id": integration_id,
        "amount_cents": amount_cents,
        "currency": currency,
        "billing_data": billing_data,
    }
    response = requests.post(payment_url, json=payment_data, headers=headers)
    if response.status_code == 201:
        payment_token = response.json().get("token")
        return iframe_id, payment_token
    else:
        raise Exception(f"Error getting payment token: {response.json()}")

def process_payment(payment_method, merchant_order_id, amount_cents, currency, billing_data, items):
    """Process payment by getting auth token, registering order, and fetching iframe URL."""
    auth_token = get_auth_token()
    order_info = {
        "merchant_order_id": merchant_order_id,
        "amount_cents": amount_cents,
        "currency": currency,
        "items": items,
    }
    order_id = register_order(auth_token, order_info)
    print(f'order__id: {order_id}')
    iframe_id, payment_token = get_payment_token(auth_token, order_id, billing_data, payment_method, amount_cents, currency)
    iframe_url = IFRAME_BASE_URL.format(iframe_id=iframe_id, payment_token=payment_token)
    return iframe_url


import logging
import hmac
import hashlib

logger = logging.getLogger('payments')

import hmac
import hashlib


def calculate_hmac(data, textType):
    concatenated_string = process_data(data, textType)
    print(f"Concatenated string for HMAC: {concatenated_string}")
    # Log concatenated string for debugging
    logger.debug(f"Concatenated string for HMAC: {concatenated_string}")

    # The following step is required for the HMAC calculation to work:
    # Encoding the strings to bytes (HMAC and hashlib require bytes, not strings)
    hmac_key_bytes = HMAC_KEY.encode("utf-8")  # Convert the HMAC key to bytes
    concatenated_bytes = concatenated_string.encode("utf-8")  # Convert the concatenated string to bytes

    print(f"Bytes for HMAC: {concatenated_bytes}")

    # Generate HMAC using SHA512
    hmac_signature = hmac.new(hmac_key_bytes, concatenated_bytes, hashlib.sha512).hexdigest()

    return hmac_signature


def process_data(data, textType):
    """
    Processes data based on whether it's a Django request object or a dictionary payload.
    
    Args:
        data: Either a Django request object (WSGIRequest) or a dictionary payload.
    
    Returns:
        A concatenated string based on the 20 keys.
    """
    result=""
    # Logic for handling a Django request
    if textType=="payload":  # Logic for handling a dictionary payload
        result = concatenate_keys_payload(data)
    if textType=="request":  # Check if it's a request object
        result = concatenate_keys_requestObj(data)

    return result

def concatenate_keys_requestObj(query_dict):
    # Convert QueryDict to a regular dictionary
    data = query_dict.dict()  # Call .dict() on query_dict, not the request object

    # Define the keys to concatenate
    keys_to_concatenate = [
        'amount_cents', 'created_at', 'currency', 'error_occured',
        'has_parent_transaction', 'id', 'integration_id', 'is_3d_secure',
        'is_auth', 'is_capture', 'is_refunded', 'is_standalone_payment',
        'is_voided', 'order', 'owner', 'pending', 'source_data.pan',
        'source_data.sub_type', 'source_data.type', 'success'
    ]

    # Concatenate values for the specified keys
    return ''.join(str(data.get(key, '')) for key in keys_to_concatenate)

def concatenate_keys_payload(payload):
    """
    Calculate the HMAC-SHA512 signature for the given payload.

    Args:
        payload (dict): The callback payload from Accept.

    Returns:
        str: The calculated HMAC.
    """
    # Specify the exact order of keys based on the API documentation
    keys = [
        "amount_cents", "created_at", "currency", "error_occured",
        "has_parent_transaction", "id", "integration_id", "is_3d_secure",
        "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
        "is_voided", "order.id", "owner", "pending", "source_data.pan",
        "source_data.sub_type", "source_data.type", "success"
    ]

    # Extract the 'obj' data
    obj_data = payload.get("obj", {})

    # Initialize a list to store the concatenated values
    concatenated_values = []

    for key in keys:
        # Handle nested keys, like 'order.id'
        key_parts = key.split(".")
        value = obj_data
        for part in key_parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

        # Convert the value to a string (use empty string if None)
        if isinstance(value, bool):
            # Convert boolean to lowercase 'true' or 'false'
            value = "true" if value else "false"
        concatenated_values.append(str(value) if value is not None else "")

    # Join all values into a single string
    concatenated_string = "".join(concatenated_values)
    return concatenated_string
import os
import ast
import uuid
from django.shortcuts import redirect
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
PAYMOB_PUBLIC_KEY= os.getenv("PAYMOB_PUBLIC_KEY")
PAYMOB_SECRET_KEY=os.getenv("PAYMOB_SECRET_KEY")
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


def process_payment(payment_method, merchant_order_id, amount_cents, currency, billing_data, items):
    BASE_URL = "https://accept.paymob.com/v1"
    url = f"{BASE_URL}/intention/"
    if payment_method not in PAYMENT_METHODS:
        raise Exception(f"Payment method '{payment_method}' is not supported.")
    
    payment_method_integration_id = int(PAYMENT_METHODS[payment_method]["integration_id"])
    print(f"Payment method integration ID: {payment_method_integration_id}")
    random_uuid = uuid.uuid4()
    special_merchant_order_id = f'{merchant_order_id}#{random_uuid}'

    payload = {
        "amount": amount_cents,
        "currency": currency,
        "special_reference": special_merchant_order_id,
        "payment_methods": [payment_method_integration_id],
        "billing_data": billing_data,
        "items": items,
    }
    
    headers = {
        "Authorization": f"Bearer {PAYMOB_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    print("here i am ------------------------------------------------------")
    response = requests.post(url, json=payload, headers=headers)
    print("here i am ------------------------------------------------------")
    print(response.json())
    logger.debug(f"Response Status: {response.status_code}")
    logger.debug(f"Response Text: {response.text}")
    response = response.json()
    client_secret = response.get('client_secret')
    print(client_secret)
    checkout_url = f"https://accept.paymob.com/unifiedcheckout/?publicKey={PAYMOB_PUBLIC_KEY}&clientSecret={client_secret}"
    return checkout_url


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
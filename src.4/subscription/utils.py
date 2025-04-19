import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from .models import CourseSubscription
from base64 import b64encode



# Static key and IV (ensure they are securely stored in a real-world app)
key = b'1234567890abcdef1234567890abcdef'  # 256-bit key (32 bytes)
iv = b'abcdef9876543210'  # 128-bit IV (16 bytes)

def encrypt_data(data):
    # Convert the data to JSON and encode it
    json_data = json.dumps(data).encode()

    # Apply padding to the data to make it block size compliant
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(json_data) + padder.finalize()

    # Create cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Encrypt the data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Return the encrypted data encoded in base64
    return  b64encode(encrypted_data).decode('utf-8')


def has_active_subscription(student, course):
    return CourseSubscription.objects.filter(
        student=student, course=course, active=True).exists()

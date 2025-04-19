from .models import Invoice
import random

def generate_sequence():
    while True:
        number = ''.join(random.choices('0123456789', k=14))
        if not Invoice.objects.filter(sequence=number).exists():
            return f'{number}'
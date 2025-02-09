# contact/forms.py
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)  # Combined name field
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)
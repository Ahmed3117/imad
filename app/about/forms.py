# contact/forms.py
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)  # Combined name field
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=False)
    phone_country_code = forms.CharField(max_length=8, required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)
    website = forms.CharField(required=False)

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise forms.ValidationError("Invalid request")
        return value

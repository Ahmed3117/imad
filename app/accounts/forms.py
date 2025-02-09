from django import forms

class SessionURLForm(forms.Form):
    session_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'id': 'sessionUrlInput',
        }),
        label='Session URL'
    )    
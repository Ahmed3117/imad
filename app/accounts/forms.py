from django import forms

from subscriptions.models import LectureNote

class SessionURLForm(forms.Form):
    session_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'id': 'sessionUrlInput',
        }),
        label='Session URL'
    )    




class LectureNoteForm(forms.ModelForm):
    class Meta:
        model = LectureNote
        fields = ['note', 'rating']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['rating'].required = False

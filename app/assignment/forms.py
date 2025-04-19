from django import forms
from .models import Assignment, StudentAnswer

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'attachment', 'due_at', 'max_grade']
        widgets = {
            'due_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class StudentAnswerForm(forms.ModelForm):
    class Meta:
        model = StudentAnswer
        fields = ['answer_text', 'attachment']

class GradeAssignmentForm(forms.ModelForm):
    class Meta:
        model = StudentAnswer
        fields = ['grade', 'teacher_feedback']
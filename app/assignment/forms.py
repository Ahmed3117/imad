from django import forms
from .models import Assignment, StudentAnswer

class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
            if field == 'description':
                self.fields[field].widget.attrs.update({
                    'rows': 3,
                    'class': 'form-control md-textarea',
                })
            elif field == 'attachment':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control-file',
                })

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'attachment', 'due_at', 'max_grade']
        widgets = {
            'due_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control datetimepicker',
            }),
        }
        labels = {
            'title': 'Assignment Title',
            'description': 'Description',
            'attachment': 'Supporting Files',
            'due_at': 'Due Date & Time',
            'max_grade': 'Maximum Grade'
        }

class StudentAnswerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
            if field == 'answer_text':
                self.fields[field].widget.attrs.update({
                    'rows': 5,
                    'class': 'form-control md-textarea',
                    'placeholder': 'Type your answer here...'
                })
            elif field == 'attachment':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control-file',
                })

    class Meta:
        model = StudentAnswer
        fields = ['answer_text', 'attachment']
        labels = {
            'answer_text': 'Your Answer',
            'attachment': 'Supporting Files'
        }

class GradeAssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
            })
            if field == 'teacher_feedback':
                self.fields[field].widget.attrs.update({
                    'rows': 3,
                    'class': 'form-control md-textarea',
                    'placeholder': 'Provide constructive feedback...'
                })

    class Meta:
        model = StudentAnswer
        fields = ['grade', 'teacher_feedback']
        labels = {
            'grade': 'Grade (Max: {{ assignment.max_grade }})',
            'teacher_feedback': 'Feedback'
        }
import os
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
                # Clear checkbox for existing files in edit form
                if self.instance and self.instance.attachment:
                    self.fields['attachment'].widget.clear_checkbox_label = "Remove current file"
                    self.fields['attachment'].widget.template_name = 'widgets/clearable_file_input.html'

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
        
        # Set common attributes for all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
            # Custom attributes for specific fields
            if field_name == 'answer_text':
                field.widget.attrs.update({
                    'rows': 5,
                    'class': 'form-control md-textarea',
                    'placeholder': 'Type your answer here...'
                })
            elif field_name == 'attachment':
                field.widget.attrs.update({
                    'class': 'form-control-file',
                    'accept': '.pdf,.doc,.docx,.txt',  # Specify allowed file types
                })
                field.help_text = 'Maximum file size: 5MB (Allowed: PDF, Word, Text)'

    class Meta:
        model = StudentAnswer
        fields = ['answer_text', 'attachment']
        labels = {
            'answer_text': 'Your Answer',
            'attachment': 'Supporting Files'
        }

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Validate file size (5MB max)
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size exceeds 5MB limit.")
            
            # Validate file extension
            valid_extensions = ['.pdf', '.doc', '.docx', '.txt']
            ext = os.path.splitext(attachment.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    "Unsupported file type. Please upload PDF, Word, or Text files."
                )
        return attachment




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



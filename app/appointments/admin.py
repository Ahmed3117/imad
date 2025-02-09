from django.contrib import admin
from django import forms
from django.forms.widgets import TimeInput
from accounts.models import User
from courses.models import Course
from .models import TeacherAvailability, Appointment
from django.utils.translation import gettext_lazy as _

class CourseFilter(admin.SimpleListFilter):
    title = _('Course')  # Display name in the admin
    parameter_name = 'course'  # URL parameter for the filter

    def lookups(self, request, model_admin):
        """
        Return a list of tuples (course_id, course_name) for the filter options.
        """
        courses = Course.objects.all()
        return [(course.id, course.name) for course in courses]

    def queryset(self, request, queryset):
        """
        Filter the queryset based on the selected course.
        """
        if self.value():
            return queryset.filter(teacher__teacher_info__courses__id=self.value())
        return queryset

class TeacherAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TeacherAvailability
        fields = '__all__'
        widgets = {
            'start_time': TimeInput(attrs={'type': 'time', 'step': '1'}),  # Time picker with seconds
            'end_time': TimeInput(attrs={'type': 'time', 'step': '1'}),  # Time picker with seconds
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Capture the request
        super().__init__(*args, **kwargs)
        if 'teacher' in self.fields:
            if self.request and self.request.user.role == 'teacher':
                self.fields['teacher'].queryset = User.objects.filter(id=self.request.user.id)
            else:
                self.fields['teacher'].queryset = User.objects.filter(role='teacher')


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        widgets = {
            'start_time': TimeInput(attrs={'type': 'time', 'step': '1'}),  # Time picker with seconds
            'end_time': TimeInput(attrs={'type': 'time', 'step': '1'}),  # Time picker with seconds
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Capture the request
        super().__init__(*args, **kwargs)
        if 'teacher' in self.fields:
            if self.request and self.request.user.role == 'teacher':
                self.fields['teacher'].queryset = User.objects.filter(id=self.request.user.id)
            else:
                self.fields['teacher'].queryset = User.objects.filter(role='teacher')

class TeacherAvailabilityAdmin(admin.ModelAdmin):
    form = TeacherAvailabilityForm
    list_display = ('teacher', 'teacher_courses', 'day', 'start_time', 'end_time', 'is_available')
    list_filter = ('day', 'is_available',CourseFilter)
    search_fields = ('teacher__username','teacher__name', 'day','is_available','teacher__teacher_info__courses__name')
    autocomplete_fields = ('teacher',)  
    readonly_fields = ('teacher_courses',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request  # Pass the request to the form
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'teacher':
            return qs.filter(teacher=request.user)
        return qs
    # Customize the form layout
    fieldsets = (
        (None, {
            'fields': ('teacher', 'day', 'start_time', 'end_time', 'is_available')
        }),
        ('Additional Information', {
            'fields': ('teacher_courses',),
            'description': 'Courses associated with the teacher.'
        }),
    )

class AppointmentAdmin(admin.ModelAdmin):
    # form = AppointmentForm
    list_display = (
        'subscription_details',
        # 'availability_details',
        'is_active',
        'student_name',
        'teacher_name',
        'course_name',
        'day_and_time'
    )
    list_filter = ('subscription', 'is_active','avialability__day')
    search_fields = (
        'subscription__student__name',
        'avialability__teacher__name',
        'avialability__day',
        'avialability__start_time',
        'avialability__end_time'
    )

    autocomplete_fields = ('subscription',)  # Make teacher and subscription fields searchable
    raw_id_fields = ('avialability', )  # Make teacher and subscription fields searchable

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request  # Pass the request to the form
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'teacher':
            return qs.filter(teacher=request.user)
        return qs

    # Custom methods to display detailed information
    def subscription_details(self, obj):
        return f"Subscription #{obj.subscription.id}"
    subscription_details.short_description = 'Subscription'

    # def availability_details(self, obj):
    #     return f"Availability #{obj.avialability.id}"
    # availability_details.short_description = 'Availability'

    def student_name(self, obj):
        return obj.subscription.student.name
    student_name.short_description = 'Student'

    def teacher_name(self, obj):
        return obj.avialability.teacher.name
    teacher_name.short_description = 'Teacher'

    def course_name(self, obj):
        return obj.subscription.course.name
    course_name.short_description = 'Course'

    def day_and_time(self, obj):
        return f"{obj.avialability.day} ({obj.avialability.start_time} - {obj.avialability.end_time})"
    day_and_time.short_description = 'Day & Time'

admin.site.register(TeacherAvailability, TeacherAvailabilityAdmin)
admin.site.register(Appointment, AppointmentAdmin)

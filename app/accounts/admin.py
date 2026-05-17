from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from about.models import FreeSession
from assignment.models import Assignment, StudentAnswer
from subscriptions.models import (
    JoinRequest,
    Lecture,
    LectureNote,
    StudyGroup,
    StudyGroupResource,
)
from .models import (
    TeacherInfo,
    TeacherInfoTranslation,
    TeacheroomAccount,
    User,
    StudentProfile,
    ZoomAccount,
)

# Inline admin for StudentProfile
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = True
    verbose_name_plural = 'Student profile'
    extra = 0


class TeacherInfoInline(admin.StackedInline):
    model = TeacherInfo
    can_delete = True
    verbose_name_plural = "Teacher public profile"
    extra = 0
    fields = ("bio", "specialization", "profile_link", "is_active_to_be_shown_in_home")


class TeacheroomAccountInline(admin.StackedInline):
    model = TeacheroomAccount
    can_delete = True
    verbose_name_plural = "Teacher Zoom account"
    extra = 0
    fields = (
        "account_id",
        "client_id",
        "client_secret",
        "secret_token",
        "verification_token",
        "is_paid",
    )

# Inline admin for ParentProfile
# class ParentProfileInline(admin.StackedInline):
#     model = ParentProfile
#     can_delete = False
#     verbose_name_plural = 'Parent Profile'
#     extra = 0

# Custom User admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'name',
        'email',
        'role',
        'phone',
        'is_active',
        'is_staff',
        'student_analysis_link',
    )
    list_filter = ('role', 'is_staff', 'is_superuser')
    list_display_links = ('username', 'name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Profile', {'fields': ('role', 'name', 'email', 'phone', 'image')}),
        ('Permissions', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'classes': ('collapse',), 'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'email', 'phone', 'role', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email', 'name', 'phone')
    ordering = ('role', 'name', 'username')
    readonly_fields = ('last_login', 'date_joined')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/student-analysis/',
                self.admin_site.admin_view(self.student_analysis_view),
                name='accounts_user_student_analysis',
            ),
        ]
        return custom_urls + urls

    def student_analysis_link(self, obj):
        if obj.role != 'student':
            return '-'
        url = reverse('admin:accounts_user_student_analysis', args=[obj.pk])
        return format_html('<a class="button" href="{}">Full analysis</a>', url)

    student_analysis_link.short_description = 'Student analysis'

    def student_analysis_view(self, request, user_id):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        student = self.get_queryset(request).filter(pk=user_id).first()
        if not student:
            messages.error(request, 'User not found.')
            return redirect('admin:accounts_user_changelist')
        if student.role != 'student':
            messages.warning(request, 'Student analysis is only available for student users.')
            return redirect(reverse('admin:accounts_user_change', args=[student.pk]))

        context = {
            **self.admin_site.each_context(request),
            'title': f'Student analysis: {student.get_name()}',
            'opts': self.model._meta,
            'student': student,
            **self._build_student_analysis_context(student),
        }
        return TemplateResponse(request, 'admin/accounts/student_analysis.html', context)

    def _build_student_analysis_context(self, student):
        now = timezone.now()
        profile = StudentProfile.objects.filter(user=student).first()
        free_session = FreeSession.objects.filter(user=student).first()
        groups = (
            StudyGroup.objects.filter(students=student)
            .distinct()
            .select_related('course__level', 'course__track', 'teacher')
            .prefetch_related('group_times')
        )
        group_ids = list(groups.values_list('id', flat=True))

        lectures = Lecture.objects.filter(group_id__in=group_ids).select_related(
            'group__course__level',
            'group__course__track',
            'group__teacher',
        )
        lecture_ids = list(lectures.values_list('id', flat=True))
        lecture_stats = lectures.aggregate(
            total=Count('id'),
            finished=Count('id', filter=Q(is_finished=True)),
            upcoming=Count('id', filter=Q(live_link_date__gt=now, is_finished=False)),
            with_links=Count('id', filter=Q(live_link__isnull=False) & ~Q(live_link='')),
        )

        teacher_notes = LectureNote.objects.filter(
            lecture_id__in=lecture_ids,
            user__role='teacher',
        ).select_related('lecture', 'lecture__group', 'user')
        student_notes = LectureNote.objects.filter(
            lecture_id__in=lecture_ids,
            user=student,
        ).select_related('lecture', 'lecture__group')

        status_counts = {
            choice_key: teacher_notes.filter(lecture_status=choice_key).count()
            for choice_key, _ in LectureNote.LECTURE_STATUS_CHOICES
        }
        completed_count = status_counts.get('completed', 0)
        reviewed_count = sum(status_counts.values())
        completion_rate = round((completed_count / reviewed_count) * 100) if reviewed_count else 0
        student_notes_count = student_notes.count()

        assignments = Assignment.objects.filter(lecture_id__in=lecture_ids).select_related(
            'lecture',
            'lecture__group',
        )
        answers = StudentAnswer.objects.filter(student=student, assignment__lecture_id__in=lecture_ids).select_related(
            'assignment',
            'assignment__lecture',
        )
        answer_stats = answers.aggregate(
            submitted=Count('id'),
            graded=Count('id', filter=Q(grade__isnull=False)),
            average_grade=Avg('grade'),
        )
        assignment_total = assignments.count()
        submitted_count = answer_stats['submitted'] or 0
        submission_rate = round((submitted_count / assignment_total) * 100) if assignment_total else 0
        answered_assignment_ids = answers.values_list('assignment_id', flat=True)
        pending_assignments = assignments.exclude(id__in=answered_assignment_ids).order_by('due_at')
        overdue_pending_count = pending_assignments.filter(due_at__lt=now).count()

        recent_lectures = lectures.order_by('-live_link_date', '-created')[:12]
        recent_teacher_notes = teacher_notes.order_by('-created_at')[:12]
        recent_student_notes = student_notes.order_by('-created_at')[:8]
        recent_answers = answers.order_by('-submitted_at')[:12]
        shared_resources = StudyGroupResource.objects.filter(studygroup_id__in=group_ids).select_related(
            'studygroup',
            'resource',
            'resource__course',
            'shared_by',
        ).order_by('-shared_at')[:12]
        join_requests = JoinRequest.objects.filter(student=student).select_related(
            'course__level',
            'course__track',
            'group',
        ).order_by('-id')

        group_summaries = []
        for group in groups:
            group_lectures = lectures.filter(group=group)
            group_assignments = assignments.filter(lecture__group=group)
            group_answers = answers.filter(assignment__lecture__group=group)
            group_summaries.append({
                'group': group,
                'lecture_count': group_lectures.count(),
                'finished_lecture_count': group_lectures.filter(is_finished=True).count(),
                'assignment_count': group_assignments.count(),
                'answer_count': group_answers.count(),
                'average_grade': group_answers.aggregate(avg=Avg('grade'))['avg'],
            })

        return {
            'profile': profile,
            'free_session': free_session,
            'groups': groups,
            'group_summaries': group_summaries,
            'lecture_stats': lecture_stats,
            'status_counts': status_counts,
            'reviewed_count': reviewed_count,
            'completion_rate': completion_rate,
            'student_notes_count': student_notes_count,
            'assignment_total': assignment_total,
            'answer_stats': answer_stats,
            'submission_rate': submission_rate,
            'pending_assignments': pending_assignments[:12],
            'pending_assignment_count': assignment_total - submitted_count,
            'overdue_pending_count': overdue_pending_count,
            'recent_lectures': recent_lectures,
            'recent_teacher_notes': recent_teacher_notes,
            'recent_student_notes': recent_student_notes,
            'recent_answers': recent_answers,
            'shared_resources': shared_resources,
            'join_requests': join_requests,
        }

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        if obj.role == 'student':
            return [StudentProfileInline]
        if obj.role == 'teacher':
            return [TeacherInfoInline, TeacheroomAccountInline]
        return []


@admin.register(ZoomAccount)
class ZoomAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'account_id', 'is_available_display', 'client_id_masked', 'client_secret_masked')
    list_filter = ('account_id',)
    search_fields = ('account_id', 'client_id')
    readonly_fields = ('is_available_display',)
    fieldsets = (
        (None, {
            'fields': ('account_id', 'client_id', 'client_secret')
        }),
        ('Tokens', {
            'fields': ('secret_token', 'verification_token')
        }),
        ('Status', {
            'fields': ('is_available_display',)
        }),
    )

    def is_available_display(self, obj):
        return obj.is_available()
    is_available_display.boolean = True
    is_available_display.short_description = 'Available'

    def client_id_masked(self, obj):
        if not obj.client_id:
            return "-"
        return f"{obj.client_id[:4]}...{obj.client_id[-4:]}"
    client_id_masked.short_description = 'Client ID'

    def client_secret_masked(self, obj):
        if not obj.client_secret:
            return "-"
        return f"{obj.client_secret[:4]}...{obj.client_secret[-4:]}"
    client_secret_masked.short_description = 'Client Secret'


# Admin for ParentProfile
# @admin.register(ParentProfile)
# class ParentProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'get_email', 'get_phone', 'type')
#     search_fields = ('user__username', 'user__email', 'user__phone')
#     list_filter = ('type',)

#     def get_email(self, obj):
#         return obj.user.email
#     get_email.short_description = 'Email'

#     def get_phone(self, obj):
#         return obj.user.phone
#     get_phone.short_description = 'Phone'


# Admin for StudentProfile
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent_phone', 'age')
    search_fields = ('user__username', 'user__email', 'user__phone')
    list_filter = ('age',)


# class ParentStudentInline(admin.TabularInline):
#     model = ParentStudent
#     extra = 1
#     fk_name = 'parent'
#     verbose_name = 'Student'
#     verbose_name_plural = 'Students'
    
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == "student":
#             kwargs["queryset"] = User.objects.filter(role='student')
#         return super().formfield_for_foreignkey(db_field, request, **kwargs)




class TeacherInfoTranslationInline(admin.TabularInline):
    model = TeacherInfoTranslation
    extra = 1

@admin.register(TeacherInfo)
class TeacherInfoAdmin(admin.ModelAdmin):
    inlines = [TeacherInfoTranslationInline]
    list_display = ('teacher', 'specialization', 'is_active_to_be_shown_in_home', 'profile_link')
    list_filter = ('specialization', 'is_active_to_be_shown_in_home')
    search_fields = ('teacher__name', 'specialization', 'bio')
    autocomplete_fields = ('teacher',)
    # filter_horizontal = ('courses',)


@admin.register(TeacheroomAccount)
class TeacheroomAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_id', 'is_paid', 'client_id_masked', 'client_secret_masked')
    list_filter = ('is_paid',)
    search_fields = ('user__username', 'user__name', 'user__email', 'account_id', 'client_id')
    autocomplete_fields = ('user',)
    fieldsets = (
        ('Teacher', {'fields': ('user', 'is_paid')}),
        ('Zoom Credentials', {'fields': ('account_id', 'client_id', 'client_secret')}),
        ('Verification', {'classes': ('collapse',), 'fields': ('secret_token', 'verification_token')}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(role='teacher').order_by('name', 'username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def client_id_masked(self, obj):
        if not obj.client_id:
            return "-"
        return f"{obj.client_id[:4]}...{obj.client_id[-4:]}"

    client_id_masked.short_description = 'Client ID'

    def client_secret_masked(self, obj):
        if not obj.client_secret:
            return "-"
        return f"{obj.client_secret[:4]}...{obj.client_secret[-4:]}"

    client_secret_masked.short_description = 'Client Secret'


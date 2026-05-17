from django.contrib import admin
from django.contrib.admin.filters import RelatedOnlyFieldListFilter
from django.contrib.auth import get_user_model

from .models import Assignment, StudentAnswer

User = get_user_model()


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    fields = (
        "student",
        "submitted_at",
        "grade",
        "teacher_feedback",
        "attachment",
    )
    readonly_fields = ("submitted_at",)
    autocomplete_fields = ("student",)
    show_change_link = True


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lecture",
        "teacher_name",
        "due_at",
        "max_grade",
        "submission_summary",
        "created_at",
    )
    list_filter = (
        "due_at",
        "created_at",
        ("lecture__group", RelatedOnlyFieldListFilter),
        ("lecture__group__teacher", RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "title",
        "description",
        "lecture__title",
        "lecture__group__name",
        "lecture__group__course__name",
        "lecture__group__teacher__username",
        "lecture__group__teacher__name",
    )
    autocomplete_fields = ("lecture",)
    readonly_fields = ("created_at", "updated_at", "submission_summary")
    date_hierarchy = "due_at"
    inlines = (StudentAnswerInline,)
    fieldsets = (
        ("Assignment", {"fields": ("lecture", "title", "description", "attachment")}),
        ("Grading", {"fields": ("due_at", "max_grade", "submission_summary")}),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("lecture__group__teacher", "lecture__group__course")
            .prefetch_related("student_answers")
        )

    def teacher_name(self, obj):
        teacher = obj.lecture.group.teacher
        return teacher.get_name() or teacher.username

    teacher_name.short_description = "Teacher"

    def submission_summary(self, obj):
        if not obj.pk:
            return "-"
        submitted = obj.student_answers.count()
        total_students = obj.lecture.group.students.count()
        graded = obj.student_answers.filter(grade__isnull=False).count()
        return f"{submitted}/{total_students} submitted, {graded} graded"

    submission_summary.short_description = "Submissions"


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "assignment",
        "lecture",
        "submitted_at",
        "grade",
        "max_grade",
        "is_late",
    )
    list_filter = (
        "submitted_at",
        "grade",
        ("assignment__lecture__group", RelatedOnlyFieldListFilter),
        ("assignment__lecture__group__teacher", RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "student__username",
        "student__name",
        "student__email",
        "assignment__title",
        "assignment__lecture__title",
        "answer_text",
        "teacher_feedback",
    )
    autocomplete_fields = ("assignment", "student")
    readonly_fields = ("submitted_at", "updated_at", "is_late", "max_grade")
    date_hierarchy = "submitted_at"
    fieldsets = (
        ("Student Submission", {"fields": ("assignment", "student", "answer_text", "attachment")}),
        ("Teacher Grading", {"fields": ("grade", "max_grade", "teacher_feedback")}),
        ("Status", {"classes": ("collapse",), "fields": ("submitted_at", "updated_at", "is_late")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("student", "assignment__lecture__group__teacher", "assignment__lecture")
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(role="student").order_by("name", "username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def lecture(self, obj):
        return obj.assignment.lecture

    lecture.short_description = "Lecture"

    def max_grade(self, obj):
        if not obj.pk:
            return "-"
        return obj.assignment.max_grade

    max_grade.short_description = "Max grade"

    def is_late(self, obj):
        if not obj.pk:
            return "-"
        return obj.submitted_at > obj.assignment.due_at

    is_late.boolean = True
    is_late.short_description = "Late"

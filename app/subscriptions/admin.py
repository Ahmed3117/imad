from django.contrib import admin, messages
from django.contrib.admin.filters import RelatedOnlyFieldListFilter
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils.html import format_html

from project.admin_helpers import UnhandledChangelistMixin, contact_link_icons
from .models import (
    GroupTime,
    JoinRequest,
    Lecture,
    LectureFile,
    LectureNote,
    LectureVisitHistory,
    StudyGroup,
    StudyGroupReport,
    StudyGroupResource,
)

User = get_user_model()


class GroupTimeInline(admin.TabularInline):
    model = GroupTime
    extra = 1
    fields = ("day", "time")
    ordering = ("day", "time")


class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 0
    fields = (
        "title",
        "live_link_date",
        "duration",
        "is_finished",
        "is_owner_link",
    )
    readonly_fields = ("title", "live_link_date", "duration", "is_finished", "is_owner_link")
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class StudyGroupResourceInline(admin.TabularInline):
    model = StudyGroupResource
    extra = 0
    fields = ("resource", "shared_by", "shared_at")
    readonly_fields = ("shared_at",)
    autocomplete_fields = ("resource", "shared_by")
    show_change_link = True


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "course_path",
        "teacher_link",
        "capacity_status",
        "schedule_summary",
        "lectures_progress",
        "average_rating",
        "report_button",
    )
    list_filter = (
        "capacity",
        ("teacher", RelatedOnlyFieldListFilter),
        ("course__level", RelatedOnlyFieldListFilter),
        ("course__track", RelatedOnlyFieldListFilter),
        ("course", RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "name",
        "course__name",
        "course__level__name",
        "course__track__name",
        "teacher__username",
        "teacher__name",
        "students__username",
        "students__name",
        "students__email",
    )
    autocomplete_fields = ("course", "teacher")
    readonly_fields = (
        "display_name",
        "student_count",
        "schedule_summary",
        "lectures_progress",
        "average_rating",
        "report_button",
    )
    filter_horizontal = ("students",)
    inlines = (GroupTimeInline, LectureInline, StudyGroupResourceInline)
    fieldsets = (
        (
            "Group Setup",
            {
                "fields": (
                    "name",
                    "course",
                    "teacher",
                    "capacity",
                    "number_of_expected_lectures",
                    "join_price",
                )
            },
        ),
        (
            "Students",
            {
                "description": "Search and add enrolled students here. Join requests with an assigned group also add students automatically when saved.",
                "fields": ("students", "student_count"),
            },
        ),
        (
            "Operational Summary",
            {
                "classes": ("collapse",),
                "fields": (
                    "display_name",
                    "schedule_summary",
                    "lectures_progress",
                    "average_rating",
                    "report_button",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("course__level", "course__track", "teacher")
            .prefetch_related("students", "group_times")
            .annotate(
                enrolled_students=Count("students", distinct=True),
                total_lectures=Count("lectures", distinct=True),
                finished_lectures=Count(
                    "lectures",
                    filter=Q(lectures__is_finished=True),
                    distinct=True,
                ),
                avg_rating=Avg("lectures__notes__rating", filter=Q(lectures__notes__rating__isnull=False)),
            )
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(role="teacher").order_by("name", "username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "students":
            kwargs["queryset"] = User.objects.filter(role="student").order_by("name", "username")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def display_name(self, obj):
        return obj.name or f"Group-{obj.pk}"

    display_name.short_description = "Group"
    display_name.admin_order_field = "name"

    def course_path(self, obj):
        level = obj.course.level.name if obj.course and obj.course.level else "No level"
        track = obj.course.track.name if obj.course and obj.course.track else "No track"
        return f"{level} / {track} / {obj.course.name}"

    course_path.short_description = "Course"
    course_path.admin_order_field = "course__name"

    def teacher_link(self, obj):
        url = reverse("admin:accounts_user_change", args=[obj.teacher_id])
        label = obj.teacher.get_name() or obj.teacher.username
        return format_html('<a href="{}">{}</a>', url, label)

    teacher_link.short_description = "Teacher"
    teacher_link.admin_order_field = "teacher__name"

    def student_count(self, obj):
        if not obj.pk:
            return 0
        return getattr(obj, "enrolled_students", obj.students.count())

    student_count.short_description = "Enrolled students"

    def capacity_status(self, obj):
        count = self.student_count(obj)
        if obj.capacity:
            return f"{count}/{obj.capacity}"
        return str(count)

    capacity_status.short_description = "Students"

    def schedule_summary(self, obj):
        if not obj.pk:
            return "-"
        times = list(obj.group_times.all())
        if not times:
            return "No meeting times set"
        return ", ".join(f"{time.get_day_display()} {time.time.strftime('%H:%M')}" for time in times)

    schedule_summary.short_description = "Meeting times"

    def lectures_progress(self, obj):
        total = getattr(obj, "total_lectures", obj.lectures.count())
        finished = getattr(obj, "finished_lectures", obj.lectures.filter(is_finished=True).count())
        expected = obj.number_of_expected_lectures
        return f"{finished}/{total} finished, {expected} expected"

    lectures_progress.short_description = "Lectures"

    def average_rating(self, obj):
        avg = getattr(obj, "avg_rating", None)
        return f"{avg:.1f}" if avg else "N/A"

    average_rating.short_description = "Avg rating"

    def report_button(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("subscriptions:studygroup_report", args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">Full report</a>', url)

    report_button.short_description = "Report"


@admin.register(JoinRequest)
class JoinRequestAdmin(UnhandledChangelistMixin, admin.ModelAdmin):
    list_display = (
        "student_link",
        "contact_links",
        "course_path",
        "group_link",
        "enrollment_status",
        "handled",
        "created_at",
    )
    list_filter = ("handled", "created_at", ("course", RelatedOnlyFieldListFilter), ("group", RelatedOnlyFieldListFilter))
    list_editable = ("handled",)
    search_fields = (
        "student__username",
        "student__name",
        "student__email",
        "student__phone",
        "student__telegram_username",
        "course__name",
        "group__name",
    )
    autocomplete_fields = ("student", "course", "group")
    readonly_fields = ("created_at",)
    ordering = ("handled", "-created_at")
    actions = ("enroll_selected_requests", "mark_as_handled", "mark_as_unhandled")
    fieldsets = (
        (
            "Request",
            {
                "fields": (
                    "student",
                    "course",
                    "group",
                    "handled",
                    "created_at",
                ),
                "description": "Assign a group and save. The student will be added to the selected group automatically.",
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student", "course__level", "course__track", "group")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(role="student").order_by("name", "username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def student_link(self, obj):
        url = reverse("admin:accounts_user_change", args=[obj.student_id])
        return format_html('<a href="{}">{}</a>', url, obj.student.get_name() or obj.student.username)

    student_link.short_description = "Student"
    student_link.admin_order_field = "student__name"

    def contact_links(self, obj):
        return contact_link_icons(
            phone=obj.student.phone,
            email=obj.student.email,
            telegram_username=getattr(obj.student, "telegram_username", ""),
        )

    contact_links.short_description = "Contact"

    def course_path(self, obj):
        level = obj.course.level.name if obj.course and obj.course.level else "No level"
        track = obj.course.track.name if obj.course and obj.course.track else "No track"
        return f"{level} / {track} / {obj.course.name}"

    course_path.short_description = "Requested course"

    def group_link(self, obj):
        if not obj.group_id:
            return "Not assigned"
        url = reverse("admin:subscriptions_studygroup_change", args=[obj.group_id])
        return format_html('<a href="{}">{}</a>', url, obj.group)

    group_link.short_description = "Assigned group"

    def enrollment_status(self, obj):
        if not obj.group_id:
            return "Needs group"
        return "Enrolled" if obj.group.students.filter(pk=obj.student_id).exists() else "Group assigned, not enrolled"

    enrollment_status.short_description = "Status"

    @admin.action(description="Enroll selected requests that already have a group")
    def enroll_selected_requests(self, request, queryset):
        enrolled = 0
        skipped = 0
        for join_request in queryset.select_related("group", "student"):
            if not join_request.group_id:
                skipped += 1
                continue
            join_request.group.students.add(join_request.student)
            if not join_request.handled:
                join_request.handled = True
                join_request.save(update_fields=["handled"])
            enrolled += 1
        self.message_user(
            request,
            f"{enrolled} request(s) enrolled. {skipped} skipped because no group was assigned.",
            messages.SUCCESS if enrolled else messages.WARNING,
        )

    @admin.action(description="Mark selected as handled")
    def mark_as_handled(self, request, queryset):
        updated = queryset.update(handled=True)
        self.message_user(request, f"{updated} request(s) marked as handled.")

    @admin.action(description="Mark selected as unhandled")
    def mark_as_unhandled(self, request, queryset):
        updated = queryset.update(handled=False)
        self.message_user(request, f"{updated} request(s) marked as unhandled.")


class LectureFileInline(admin.TabularInline):
    model = LectureFile
    extra = 0
    fields = ("file",)


class LectureNoteInline(admin.TabularInline):
    model = LectureNote
    extra = 0
    fields = ("user", "note", "rating", "lecture_status", "delay_reason", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)
    show_change_link = True


class LectureVisitHistoryInline(admin.TabularInline):
    model = LectureVisitHistory
    extra = 0
    fields = ("user", "visited_at")
    readonly_fields = ("user", "visited_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "group",
        "teacher_name",
        "live_link_date",
        "duration",
        "link_status",
        "is_finished",
        "rating_summary",
    )
    list_filter = (
        "is_finished",
        "is_owner_link",
        ("group", RelatedOnlyFieldListFilter),
        ("group__teacher", RelatedOnlyFieldListFilter),
        "created",
    )
    search_fields = (
        "title",
        "description",
        "group__name",
        "group__course__name",
        "group__teacher__username",
        "group__teacher__name",
    )
    autocomplete_fields = ("group", "zoom_account")
    readonly_fields = ("created", "link_status", "meeting_id", "rating_summary")
    date_hierarchy = "live_link_date"
    inlines = (LectureFileInline, LectureNoteInline, LectureVisitHistoryInline)
    fieldsets = (
        ("Lecture", {"fields": ("group", "title", "description", "duration", "created")}),
        (
            "Live Session",
            {
                "fields": (
                    "live_link",
                    "live_link_date",
                    "is_owner_link",
                    "zoom_account",
                    "link_valid_until",
                    "link_status",
                    "meeting_id",
                )
            },
        ),
        ("Completion", {"fields": ("is_finished", "finished_date", "is_visited", "rating_summary")}),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("group__teacher", "group__course", "zoom_account")
        if request.user.is_superuser or getattr(request.user, "role", None) == "admin":
            return queryset
        return queryset.filter(group__teacher=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "group" and not request.user.is_superuser and getattr(request.user, "role", None) != "admin":
            kwargs["queryset"] = StudyGroup.objects.filter(teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        filters = ["is_finished", "is_owner_link", "created"]
        if request.user.is_superuser or getattr(request.user, "role", None) == "admin":
            filters.insert(0, ("group", RelatedOnlyFieldListFilter))
            filters.insert(1, ("group__teacher", RelatedOnlyFieldListFilter))
        else:
            filters.insert(0, ("group", RelatedOnlyFieldListFilter))
        return filters

    def teacher_name(self, obj):
        return obj.group.teacher.get_name() or obj.group.teacher.username

    teacher_name.short_description = "Teacher"

    def link_status(self, obj):
        if not obj.pk:
            return "-"
        return obj.get_link_status()

    link_status.short_description = "Link status"

    def meeting_id(self, obj):
        if not obj.pk:
            return "-"
        return obj.get_meeting_id() or "-"

    meeting_id.short_description = "Meeting ID"

    def rating_summary(self, obj):
        if not obj.pk:
            return "-"
        count = obj.get_rating_count()
        if not count:
            return "No ratings"
        return f"{obj.get_average_rating():.1f} from {count} rating(s)"

    rating_summary.short_description = "Rating"


@admin.register(StudyGroupReport)
class StudyGroupReportAdmin(admin.ModelAdmin):
    list_display = ("study_group", "last_reported_date", "updated_at")
    list_filter = ("last_reported_date", "updated_at")
    search_fields = ("study_group__name", "study_group__course__name", "study_group__teacher__username")
    autocomplete_fields = ("study_group",)
    readonly_fields = ("updated_at",)

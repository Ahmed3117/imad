from django.contrib import admin
from .models import LectureNote, StudyGroup, GroupTime, JoinRequest, Lecture, LectureFile
from django.contrib.admin.filters import RelatedOnlyFieldListFilter
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import render
from django.db.models import Avg, Count, Q

# Custom admin for StudyGroup
class GroupTimeInline(admin.TabularInline):
    model = GroupTime
    extra = 1

class StudyGroupAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'course', 
        'capacity', 
        'teacher', 
        'number_of_expected_lectures', 
        'join_price',
        'lectures_count',
        'finished_lectures_count',
        'average_rating',
        'report_button'
    )
    search_fields = ('course__name', 'teacher__username', 'teacher__name')
    list_filter = ('capacity', 'course', 'teacher')
    filter_horizontal = ('students',)
    inlines = [GroupTimeInline]
    
    def lectures_count(self, obj):
        return obj.lectures.count()
    lectures_count.short_description = 'Total Lectures'
    
    def finished_lectures_count(self, obj):
        return obj.lectures.filter(is_finished=True).count()
    finished_lectures_count.short_description = 'Finished Lectures'
    
    def average_rating(self, obj):
        avg = obj.lectures.aggregate(
            avg_rating=Avg('notes__rating', filter=Q(notes__rating__isnull=False)))
        return f"{avg['avg_rating']:.1f}" if avg['avg_rating'] else "N/A"
    average_rating.short_description = 'Avg Rating'
    
    def report_button(self, obj):
        return format_html(
            '<a class="button" href="{}" target="_blank">View Full Report</a>',
            reverse('subscriptions:studygroup_report', args=[obj.pk])
        )
    report_button.short_description = 'Report'
    report_button.allow_tags = True



# Custom admin for GroupTime
class GroupTimeAdmin(admin.ModelAdmin):
    list_display = ('group', 'day', 'time')
    search_fields = ('group__course__name', 'group__teacher__username')
    list_filter = ('day', 'group__teacher')

# Custom admin for JoinRequest
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'group')
    search_fields = ('student__username', 'course__name', 'group__course__name')
    list_filter = ('course', 'group')
    # autocomplete_fields = ('student', 'course', 'group')
    raw_id_fields = ('group',)

# Custom admin for Lecture
class LectureFileInline(admin.TabularInline):
    model = LectureFile
    extra = 1

from django.contrib import admin
from .models import Lecture, LectureFile, StudyGroup
from .models import StudyGroupResource

class LectureFileInline(admin.TabularInline):
    model = LectureFile
    extra = 1

class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created', 'group', 'live_link')
    search_fields = ('title', 'description', 'group__course__name')
    list_filter = ('group', 'created')
    readonly_fields = ('created',)
    inlines = [LectureFileInline,]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(group__teacher=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit the groups shown in the lecture admin to only those taught by the teacher."""
        if db_field.name == "group" and not request.user.is_superuser:
            kwargs["queryset"] = StudyGroup.objects.filter(teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        """Limit the group filter dropdown to only relevant groups for teachers."""
        filters = ['created']
        if request.user.is_superuser:
            filters.insert(0, 'group')
        else:
            filters.insert(0, ('group', RelatedOnlyFieldListFilter))  # Show only related groups
        return filters





    # def has_module_permission(self, request):
    #     if request.user:
    #         return request.user.role == "teacher"

    # def has_view_permission(self, request, obj=None):
    #     return request.user.is_superuser or (obj and obj.group.teacher == request.user)

    # def has_add_permission(self, request):
    #     if request.user:
    #         return request.user.role == "teacher"

    # def has_change_permission(self, request, obj=None):
    #     return request.user.is_superuser or (obj and obj.group.teacher == request.user)

    # def has_delete_permission(self, request, obj=None):
    #     return request.user.is_superuser or (obj and obj.group.teacher == request.user)

class StudyGroupResourceAdmin(admin.ModelAdmin):
    list_display = ('studygroup', 'resource', 'shared_by', 'shared_at')
    search_fields = ('studygroup__name', 'resource__file', 'shared_by__username')
    list_filter = ('shared_at', 'studygroup')



# Register the models with their custom admins
admin.site.register(GroupTime, GroupTimeAdmin)
admin.site.register(JoinRequest, JoinRequestAdmin)
admin.site.register(Lecture, LectureAdmin)
admin.site.register(StudyGroup, StudyGroupAdmin)
admin.site.register(StudyGroupResource, StudyGroupResourceAdmin)
# admin.site.register(LectureFile, LectureFileAdmin)

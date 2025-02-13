from django.contrib import admin
from .models import StudyGroup, GroupTime, JoinRequest, Lecture, LectureFile
from django.contrib.admin.filters import RelatedOnlyFieldListFilter

# Custom admin for StudyGroup
class GroupTimeInline(admin.TabularInline):
    model = GroupTime
    extra = 1

class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('course', 'capacity', 'teacher', 'number_of_expected_lectures', 'join_price')
    search_fields = ('course__name', 'teacher__username' , 'teacher__name')
    list_filter = ('capacity','course', 'teacher',)
    filter_horizontal = ('students',)
    inlines = [GroupTimeInline,]

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


# Register the models with their custom admins
admin.site.register(GroupTime, GroupTimeAdmin)
admin.site.register(JoinRequest, JoinRequestAdmin)
admin.site.register(Lecture, LectureAdmin)
admin.site.register(StudyGroup, StudyGroupAdmin)
# admin.site.register(LectureFile, LectureFileAdmin)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from subscriptions.models import LectureVisitHistory
from .models import TeacherInfoTranslation, TeacheroomAccount, User, StudentProfile, ZoomAccount

# Inline admin for StudentProfile
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = True
    verbose_name_plural = 'Student Profile'
    extra = 0

# Inline admin for ParentProfile
# class ParentProfileInline(admin.StackedInline):
#     model = ParentProfile
#     can_delete = False
#     verbose_name_plural = 'Parent Profile'
#     extra = 0

# Custom User admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'name', 'role', 'phone', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'phone', 'image')}),
        ('Role', {'fields': ('role',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    search_fields = ('username', 'email', 'name')
    ordering = ('username',)

    def get_inlines(self, request, obj=None):
        """Show inlines based on the role."""
        if obj:
            # if obj.role == 'parent':
            #     return [ParentProfileInline, ParentStudentInline]
            # elif obj.role == 'student':
                # return [StudentProfileInline]
            return [StudentProfileInline]
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
        return f"{obj.client_id[:4]}...{obj.client_id[-4:]}"
    client_id_masked.short_description = 'Client ID'

    def client_secret_masked(self, obj):
        return f"{obj.client_secret[:4]}...{obj.client_secret[-4:]}"
    client_secret_masked.short_description = 'Client Secret'


@admin.register(LectureVisitHistory)
class LectureVisitHistoryAdmin(admin.ModelAdmin):
    list_display = ('lecture', 'user', 'visited_at')
    list_filter = ('lecture__group', 'user')
    search_fields = ('lecture__title', 'user__username')
    date_hierarchy = 'visited_at'

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
    list_display = ('user', 'get_parent_name', 'age')
    search_fields = ('user__username', 'user__email', 'user__phone')
    list_filter = ('age',)

    def get_parent_name(self, obj):
        parent_student = ParentStudent.objects.filter(student=obj.user).first()
        if parent_student:
            return parent_student.parent.name
        return "No Parent"
    get_parent_name.short_description = 'Parent Name'


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




from .models import TeacherInfo

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
    
# admin for teacheroom account
admin.site.register(TeacheroomAccount)


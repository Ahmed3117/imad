from django.contrib import admin
from django.contrib.auth import get_user_model
from unfold.admin import ModelAdmin, TabularInline

from .models import CourseLibrary, LibraryCategory, MyLibrary

User = get_user_model()


@admin.register(LibraryCategory)
class LibraryCategoryAdmin(ModelAdmin):
    list_display = ('name', 'resources_count', 'description')
    search_fields = ('name',)

    def resources_count(self, obj):
        return obj.libraries.count()

    resources_count.short_description = 'Resources'


class CourseLibraryInline(TabularInline):
    model = CourseLibrary
    extra = 0
    fields = ('file', 'category')
    show_change_link = True


@admin.register(CourseLibrary)
class CourseLibraryAdmin(ModelAdmin):
    list_display = ('get_file_name', 'course', 'category')
    list_filter = ('category', 'course__level', 'course__track', 'course')
    search_fields = ('course__name', 'file', 'category__name')
    autocomplete_fields = ('course', 'category')
    fieldsets = (
        ('Resource', {'fields': ('course', 'category', 'file')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course__level', 'course__track', 'category')

    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1]

    get_file_name.short_description = 'File Name'


@admin.register(MyLibrary)
class MyLibraryAdmin(ModelAdmin):
    list_display = ('get_file_name', 'user', 'course')
    list_filter = ('course__level', 'course__track', 'course', 'user')
    search_fields = ('user__username', 'user__name', 'course__name', 'file')
    autocomplete_fields = ('user', 'course')
    fieldsets = (
        ('Teacher File', {'fields': ('user', 'course', 'file')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'course__level', 'course__track')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.filter(role='teacher').order_by('name', 'username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1]

    get_file_name.short_description = 'File Name'

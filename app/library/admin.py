from django.contrib import admin
from .models import CourseLibrary, LibraryCategory, MyLibrary

# Register CourseLibrary model
@admin.register(LibraryCategory)
class LibraryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(CourseLibrary)
class CourseLibraryAdmin(admin.ModelAdmin):
    list_display = ('course', 'file', 'get_file_name', 'category')
    list_filter = ('course', 'category')  # Add category filter
    search_fields = ('course__name', 'file', 'category__name')
    
    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1]
    get_file_name.short_description = 'File Name'

# Register MyLibrary model
@admin.register(MyLibrary)
class MyLibraryAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'file', 'get_file_name')
    list_filter = ('user', 'course')
    search_fields = ('user__username', 'course__name', 'file')
    
    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1]  # Display only the file name, not the full path
    get_file_name.short_description = 'File Name'



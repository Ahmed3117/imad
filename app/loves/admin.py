from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import LoveTrack, LoveCourse

@admin.register(LoveTrack)
class LoveTrackAdmin(admin.ModelAdmin):
    list_display = ('student', 'track')
    list_filter = ('student', 'track')
    search_fields = ('student__username', 'track__name')

@admin.register(LoveCourse)
class LoveCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course')
    list_filter = ('student', 'course')
    search_fields = ('student__username', 'course__name')
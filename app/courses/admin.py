from django.contrib import admin

from library.models import CourseLibrary, MyLibrary
from .models import (
    CourseTranslation, Level, LevelTranslation, Track, Course, TrackTranslation,
)

class LevelTranslationInline(admin.TabularInline):
    model = LevelTranslation
    extra = 1

class TrackTranslationInline(admin.TabularInline):
    model = TrackTranslation
    extra = 1

class CourseTranslationInline(admin.TabularInline):
    model = CourseTranslation
    extra = 1

class CourseLibraryInline(admin.TabularInline):
    model = CourseLibrary
    extra = 1



@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    inlines = [LevelTranslationInline]
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    inlines = [TrackTranslationInline]
    list_display = ('name', 'level')
    search_fields = ('name',)
    list_filter = ('level',)
    ordering = ('name',)
    autocomplete_fields = ('level',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseTranslationInline, CourseLibraryInline]
    list_display = ('name', 'level', 'track')
    search_fields = ('name', 'description')
    list_filter = ('level', 'track')
    ordering = ('name',)
    autocomplete_fields = ('level', 'track')
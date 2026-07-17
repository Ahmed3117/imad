from django.contrib import admin
from django.db.models import Count
from project.admin_base import ModelAdmin
from unfold.admin import StackedInline, TabularInline

from library.models import CourseLibrary
from .models import (
    CourseTranslation, Level, LevelTranslation, Track, Course, TrackTranslation,
)


class LevelTranslationInline(TabularInline):
    model = LevelTranslation
    extra = 0
    tab = True
    fields = ('language', 'translated_name')


class TrackTranslationInline(TabularInline):
    model = TrackTranslation
    extra = 0
    tab = True
    fields = ('language', 'translated_name')


class CourseTranslationInline(TabularInline):
    model = CourseTranslation
    extra = 0
    tab = True
    fields = ('language', 'translated_name', 'translated_description')


class CourseLibraryInline(TabularInline):
    model = CourseLibrary
    extra = 0
    tab = True
    fields = ('file', 'category')
    show_change_link = True


@admin.register(Level)
class LevelAdmin(ModelAdmin):
    inlines = [LevelTranslationInline]
    list_display = ('name', 'tracks_count', 'courses_count')
    search_fields = ('name',)
    ordering = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            tracks_total=Count('tracks', distinct=True),
            courses_total=Count('courses', distinct=True),
        )

    def tracks_count(self, obj):
        return obj.tracks_total

    tracks_count.short_description = 'Tracks'

    def courses_count(self, obj):
        return obj.courses_total

    courses_count.short_description = 'Courses'


@admin.register(Track)
class TrackAdmin(ModelAdmin):
    inlines = [TrackTranslationInline]
    list_display = ('name', 'level', 'courses_count')
    search_fields = ('name', 'level__name')
    list_filter = ('level',)
    ordering = ('name',)
    autocomplete_fields = ('level',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('level').annotate(
            courses_total=Count('courses', distinct=True)
        )

    def courses_count(self, obj):
        return obj.courses_total

    courses_count.short_description = 'Courses'


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    inlines = [CourseTranslationInline, CourseLibraryInline]
    list_display = ('name', 'level', 'display_tracks', 'study_groups_count')
    search_fields = ('name', 'description')
    list_filter = ('level', 'tracks')
    ordering = ('name',)
    autocomplete_fields = ('level', 'tracks')
    fieldsets = (
        ('Course Identity', {'fields': ('name', 'level', 'tracks')}),
        ('Content', {'fields': ('description', 'image', 'preview_video')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('level').prefetch_related('tracks').annotate(
            groups_total=Count('study_groups', distinct=True),
        )

    def study_groups_count(self, obj):
        return obj.groups_total

    study_groups_count.short_description = 'Groups'

    def display_tracks(self, obj):
        return ", ".join([t.name for t in obj.tracks.all()])

    display_tracks.short_description = 'Tracks'

from django.contrib import admin
from .models import Subscription, SubscriptionSession


class SubscriptionSessionInline(admin.TabularInline):
    model = SubscriptionSession
    extra = 1
    autocomplete_fields = ('session',)  # Make the session field searchable if it exists


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'progress')  # Key fields in list view
    list_filter = ('status', 'course')  # Filters for status and course
    search_fields = ('student__username', 'course__name')  # Search by student username and course name
    ordering = ('student', 'course')  # Default ordering by student and course
    autocomplete_fields = ('student', 'course')  # Make student and course fields searchable
    inlines = [SubscriptionSessionInline]

    def is_completed(self, obj):
        return obj.is_completed

    is_completed.boolean = True

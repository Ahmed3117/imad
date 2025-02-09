from django.contrib import admin
from django import forms

from .models import (
    CourseTranslation, Level, LevelContent, LevelContentTranslation, LevelTranslation, SessionTranslation, Track, Course, DiscountCourse, DiscountTrack, DiscountLevel,
    Session, TrackTranslation,
)

class DiscountCourseInline(admin.TabularInline):
    model = DiscountCourse
    max_num = 1


class DiscountTrackInline(admin.TabularInline):
    model = DiscountTrack
    max_num = 1


class DiscountLevelInline(admin.TabularInline):
    model = DiscountLevel
    max_num = 1


class SessionInlineForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = '__all__'

    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}))  # Set to 2 rows

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    form = SessionInlineForm  # Use the custom form with 2 rows for content



class LevelTranslationInline(admin.TabularInline):
    model = LevelTranslation
    extra = 1

class TrackTranslationInline(admin.TabularInline):
    model = TrackTranslation
    extra = 1

class CourseTranslationInline(admin.TabularInline):
    model = CourseTranslation
    extra = 1

class SessionTranslationInline(admin.TabularInline):
    model = SessionTranslation
    extra = 1

class LevelContentTranslationInline(admin.TabularInline):
    model = LevelContentTranslation
    extra = 1

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    inlines = [LevelTranslationInline, DiscountLevelInline]
    list_display = ('name', 'year_limit', 'price_without_any_discount', 'discount_percent', 'get_final_price_after_discount')
    search_fields = ('name', 'description', 'year_limit')
    list_filter = ('year_limit',)
    ordering = ('name', 'year_limit')
    readonly_fields = ('price_without_any_discount', 'get_final_price_after_discount')

    def get_final_price_after_discount(self, obj):
        return obj.final_price_after_discound

    get_final_price_after_discount.short_description = "Price after level Discount"


@admin.register(LevelContent)
class LevelContentAdmin(admin.ModelAdmin):
    inlines = [LevelContentTranslationInline]
    list_display = ('name', 'level')
    search_fields = ('name',)
    list_filter = ('level',)
    ordering = ('name',)
    autocomplete_fields = ('level',)

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    inlines = [TrackTranslationInline, DiscountTrackInline]
    list_display = ('name', 'level', 'discount_percent', 'price_without_any_discount', 'get_final_price_after_discount')
    search_fields = ('name', 'description')
    list_filter = ('level',)
    ordering = ('name',)
    readonly_fields = ('price_without_any_discount', 'get_final_price_after_discount')
    autocomplete_fields = ('level',)

    def get_final_price_after_discount(self, obj):
        return obj.final_price_after_discound

    get_final_price_after_discount.short_description = "Price after Track Discount"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseTranslationInline, SessionInline, DiscountCourseInline]
    list_display = ('name', 'level', 'track', 'price_without_any_discount', 'discount_percent', 'get_final_price_after_discount')
    search_fields = ('name', 'description')
    list_filter = ('level', 'track')
    ordering = ('name',)
    readonly_fields = ('price_without_any_discount', 'get_final_price_after_discount')
    autocomplete_fields = ('level', 'track')

    def get_final_price_after_discount(self, obj):
        return obj.final_price_after_discound

    get_final_price_after_discount.short_description = "Final Price After Discount"

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    inlines = [SessionTranslationInline]
    search_fields = ('title', 'course__name')
    list_display = ('title', 'course', 'order')
    list_filter = ('course__level', 'course__track')
    ordering = ('order', 'title')
    autocomplete_fields = ('course',)

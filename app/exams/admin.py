from django.contrib import admin
from .models import Exam, Question, Option, ExamResult

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    inlines = [OptionInline]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    # inlines = [QuestionInline]
    list_display = ('name', 'session', 'duration')
    search_fields = ('name', 'session__title')  # Searchable session title
    list_filter = ('session__course__level', 'session__course__track')
    ordering = ('name',)  # Default ordering by name
    autocomplete_fields = ('session',)  # Make session field searchable


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ('text', 'exam')
    search_fields = ('text', 'exam__name')  # Searchable text and exam name
    list_filter = ('exam','exam__session','exam__session__course', 'exam__session__course__track','exam__session__course__level')
    ordering = ('exam', 'text')  # Default ordering by exam and question text
    autocomplete_fields = ('exam',)  # Make exam field searchable


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'is_completed')
    search_fields = ('student__username', 'exam__name')  # Searchable student and exam name
    list_filter = ('student__role', 'exam__session__course__level', 'exam__session__course__track')
    ordering = ('student', 'exam')  # Default ordering by student and exam
    autocomplete_fields = ('student', 'exam')  # Make student and exam fields searchable

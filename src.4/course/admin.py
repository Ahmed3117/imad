from django.contrib import admin
from .models import *
# Register your models here.
class CourseCodeAdmin(admin.ModelAdmin):
    search_fields = ['title']

admin.site.register(Course)
admin.site.register(Unit)
admin.site.register(Lesson)
admin.site.register(File)
admin.site.register(CourseCollection)
admin.site.register(CourseCollectionCode)
admin.site.register(CourseCategory)
admin.site.register(CourseCode,CourseCodeAdmin)
admin.site.register(LessonCode)
admin.site.register(LessonFile)
admin.site.register(AnyLessonCode)
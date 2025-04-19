from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Year)
admin.site.register(TypeEducation)
admin.site.register(StudentCode)
admin.site.register(UserActivity)


@admin.register(Student) 
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "by_code","user","active", "block","code")
    list_filter = ("by_code", )
    ordering = ("-created",)
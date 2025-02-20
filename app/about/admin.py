from django.contrib import admin

from .models import (
    CompanyInfo, CompanyInfoTranslation
)

class CompanyInfoTranslationInline(admin.TabularInline):
    model = CompanyInfoTranslation
    extra = 1

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    inlines = [CompanyInfoTranslationInline]
    list_display = ['name', 'email', 'phone']

# class PolicyTranslationInline(admin.TabularInline):
#     model = PolicyTranslation
#     extra = 1

# @admin.register(Policy)
# class PolicyAdmin(admin.ModelAdmin):
#     inlines = [PolicyTranslationInline]
#     list_display = ['policy_type', 'last_updated']
#     list_filter = ['policy_type']
#     readonly_fields = ['last_updated']




from django.db.models.signals import post_migrate
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

@receiver(post_migrate)
def remove_unwanted_permissions(sender, **kwargs):
    models_to_remove = [
        "session", "group", "logentry", "theme", "contenttype", "permission",
        "parentprofile", "studentprofile", "parentstudent",
        "teacherinfotranslation", "leveltranslation", "tracktranslation", "coursetranslation"
    ]

    # Delete permissions related to these models
    Permission.objects.filter(content_type__model__in=models_to_remove).delete()

    # Delete content types to fully remove them from admin permissions
    ContentType.objects.filter(model__in=models_to_remove).delete()



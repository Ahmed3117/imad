from django.contrib import admin
from .models import (
    CompanyInfo, CompanyInfoTranslation, PolicyTranslation,
    Policy
)

class CompanyInfoTranslationInline(admin.TabularInline):
    model = CompanyInfoTranslation
    extra = 1

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    inlines = [CompanyInfoTranslationInline]
    list_display = ['name', 'email', 'phone']

class PolicyTranslationInline(admin.TabularInline):
    model = PolicyTranslation
    extra = 1

@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    inlines = [PolicyTranslationInline]
    list_display = ['policy_type', 'last_updated']
    list_filter = ['policy_type']
    readonly_fields = ['last_updated']





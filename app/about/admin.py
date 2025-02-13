from django.contrib import admin
from .models import (
    CompanyInfo, CompanyInfoTranslation,
    CompanyDescription, CompanyDescriptionTranslation, FinalProject, FinalProjectTranslation, PolicyTranslation,
    SocialAccount, Tech, TechTranslation,
    TechUsage, TechUsageTranslation,
    Policy
)

class CompanyInfoTranslationInline(admin.TabularInline):
    model = CompanyInfoTranslation
    extra = 1

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    inlines = [CompanyInfoTranslationInline]
    list_display = ['name', 'email', 'phone']

class CompanyDescriptionTranslationInline(admin.TabularInline):
    model = CompanyDescriptionTranslation
    extra = 1

@admin.register(CompanyDescription)
class CompanyDescriptionAdmin(admin.ModelAdmin):
    inlines = [CompanyDescriptionTranslationInline]
    list_display = ['title', 'order']
    ordering = ['order']

@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ['platform_name', 'country_code', 'url']

class TechTranslationInline(admin.TabularInline):
    model = TechTranslation
    extra = 1

@admin.register(Tech)
class TechAdmin(admin.ModelAdmin):
    inlines = [TechTranslationInline]
    list_display = ['name', 'color']

class TechUsageTranslationInline(admin.TabularInline):
    model = TechUsageTranslation
    extra = 1

@admin.register(TechUsage)
class TechUsageAdmin(admin.ModelAdmin):
    inlines = [TechUsageTranslationInline]
    list_display = ['name', 'tech']

class PolicyTranslationInline(admin.TabularInline):
    model = PolicyTranslation
    extra = 1

@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    inlines = [PolicyTranslationInline]
    list_display = ['policy_type', 'last_updated']
    list_filter = ['policy_type']
    readonly_fields = ['last_updated']


class FinalProjectTranslationInline(admin.TabularInline):
        model = FinalProjectTranslation
        extra = 1

@admin.register(FinalProject)
class FinalProjectAdmin(admin.ModelAdmin):
    inlines = [FinalProjectTranslationInline]
    list_display = ['title', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title']


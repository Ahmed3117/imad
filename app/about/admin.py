from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    CompanyInfo,
    CompanyInfoTranslation,
    FreeSession,
    HomePageContent,
    HomePageContentTranslation,
    HomePageFeature,
    HomePageFeatureTranslation,
    HomePageVideoPoint,
    HomePageVideoPointTranslation,
)


class CompanyInfoTranslationInline(admin.TabularInline):
    model = CompanyInfoTranslation
    extra = 1


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    inlines = [CompanyInfoTranslationInline]
    list_display = ["name", "email", "phone"]


class HomePageContentTranslationInline(admin.StackedInline):
    model = HomePageContentTranslation
    extra = 1
    fieldsets = (
        (
            "Hero",
            {
                "fields": (
                    "language",
                    "hero_badge",
                    "hero_title",
                    "hero_description",
                    "hero_primary_button_text",
                    "hero_side_title",
                    "hero_side_description",
                    "hero_trust_badge_1",
                    "hero_trust_badge_2",
                    "hero_trust_badge_3",
                    "hero_trust_badge_4",
                    "hero_pricing_note",
                )
            },
        ),
        (
            "Primary Features",
            {
                "fields": (
                    "primary_features_title",
                    "primary_features_description",
                    "primary_features_empty_text",
                )
            },
        ),
        (
            "Who We Are",
            {
                "fields": (
                    "who_we_are_title",
                    "who_we_are_lead",
                    "who_we_are_description",
                    "who_we_are_button_text",
                )
            },
        ),
        (
            "Video",
            {
                "fields": (
                    "video_section_title",
                    "video_section_description",
                    "video_point_fallback",
                )
            },
        ),
        (
            "Chat",
            {
                "fields": (
                    "chat_section_title",
                    "chat_section_description_1",
                    "chat_section_description_2",
                    "chat_button_text",
                )
            },
        ),
        (
            "Secondary Features",
            {
                "fields": (
                    "secondary_features_title",
                    "secondary_features_description",
                    "secondary_features_empty_text",
                )
            },
        ),
        (
            "Teachers, Testimonials, and Process",
            {
                "fields": (
                    "teachers_section_title",
                    "teachers_section_subtitle",
                    "testimonials_section_title",
                    "testimonials_section_subtitle",
                    "process_section_title",
                    "process_section_description",
                )
            },
        ),
        (
            "Free Session CTA",
            {
                "fields": (
                    "free_session_section_badge",
                    "free_session_section_title",
                    "free_session_section_description",
                    "free_session_privacy_note",
                )
            },
        ),
        (
            "Family Bundle",
            {
                "fields": (
                    "family_bundle_section_badge",
                    "family_bundle_section_title",
                    "family_bundle_section_description",
                    "family_bundle_section_pricing_note_1",
                    "family_bundle_section_pricing_note_2",
                    "family_bundle_section_pricing_note_3",
                    "family_bundle_section_pricing_note_4",
                    "family_bundle_plans_title",
                    "family_bundle_plans_description",
                    "family_bundle_comparison_title",
                    "family_bundle_comparison_description",
                    "family_bundle_faq_title",
                    "family_bundle_faq_description",
                    "family_bundle_cta_title",
                    "family_bundle_cta_description",
                    "family_bundle_cta_button_text",
                )
            },
        ),
        (
            "Contact and Footer",
            {
                "fields": (
                    "contact_section_title",
                    "contact_section_description",
                    "contact_info_title",
                    "contact_info_description",
                    "facebook_label",
                    "footer_description",
                    "footer_cta_text",
                    "footer_created_by_text",
                    "footer_copyright_text",
                )
            },
        ),
    )


class HomePageFeatureTranslationInline(admin.TabularInline):
    model = HomePageFeatureTranslation
    extra = 1
    fields = ("language", "title", "subtitle", "meta", "description")


class HomePageFeatureInline(admin.StackedInline):
    model = HomePageFeature
    extra = 1
    fields = ("section", "icon_class", "image", "order", "is_active")
    show_change_link = True


class HomePageVideoPointTranslationInline(admin.TabularInline):
    model = HomePageVideoPointTranslation
    extra = 1


class HomePageVideoPointInline(admin.StackedInline):
    model = HomePageVideoPoint
    extra = 1
    fields = ("icon_class", "order", "is_active")
    show_change_link = True


@admin.register(HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "show_primary_features",
        "show_who_we_are_section",
        "show_video_section",
        "show_chat_section",
        "show_secondary_features",
        "show_teachers_section",
        "show_contact_section",
        "updated_at",
    )
    search_fields = (
        "translations__hero_title",
        "translations__family_bundle_section_title",
    )
    inlines = [
        HomePageContentTranslationInline,
        HomePageFeatureInline,
        HomePageVideoPointInline,
    ]
    fieldsets = (
        (
            "Media",
            {
                "fields": (
                    "hero_background_image",
                    "who_we_are_image",
                    "video_cover_image",
                    "intro_video",
                    "chat_image",
                    "contact_illustration",
                )
            },
        ),
        (
            "Links",
            {
                "fields": (
                    "hero_primary_button_url",
                    "who_we_are_button_url",
                    "footer_cta_url",
                    "facebook_url",
                )
            },
        ),
        (
            "Section Visibility",
            {
                "fields": (
                    "show_primary_features",
                    "show_who_we_are_section",
                    "show_video_section",
                    "show_chat_section",
                    "show_secondary_features",
                    "show_teachers_section",
                    "show_contact_section",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        if HomePageContent.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(HomePageFeature)
class HomePageFeatureAdmin(admin.ModelAdmin):
    list_display = ("id", "section", "icon_class", "order", "is_active", "home_page")
    list_filter = ("section", "is_active")
    search_fields = ("icon_class",)
    ordering = ("section", "order", "id")
    inlines = [HomePageFeatureTranslationInline]


@admin.register(HomePageVideoPoint)
class HomePageVideoPointAdmin(admin.ModelAdmin):
    list_display = ("id", "icon_class", "order", "is_active", "home_page")
    list_filter = ("is_active",)
    search_fields = ("icon_class",)
    ordering = ("order", "id")
    inlines = [HomePageVideoPointTranslationInline]


@admin.register(FreeSession)
class FreeSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "user_phone", "status", "requested_at", "marked_done_at")
    list_filter = ("status",)
    search_fields = ("user__name", "user__username", "user__email", "phone")
    ordering = ("-requested_at",)
    readonly_fields = ("user", "phone", "message", "requested_at")
    actions = ["mark_as_done"]

    def user_phone(self, obj):
        return obj.phone or obj.user.phone or "—"

    user_phone.short_description = "Phone"

    @admin.action(description="Mark selected requests as Done")
    def mark_as_done(self, request, queryset):
        updated = queryset.filter(status="pending").update(
            status="done",
            marked_done_at=timezone.now(),
        )
        self.message_user(request, f"{updated} request(s) marked as done.")

    fieldsets = (
        (
            "User Info",
            {
                "fields": ("user", "phone", "message"),
            },
        ),
        (
            "Status",
            {
                "fields": ("status", "requested_at", "marked_done_at"),
            },
        ),
    )


@receiver(post_migrate)
def remove_unwanted_permissions(sender, **kwargs):
    models_to_remove = [
        "session",
        "group",
        "logentry",
        "theme",
        "contenttype",
        "permission",
        "parentprofile",
        "studentprofile",
        "parentstudent",
        "teacherinfotranslation",
        "leveltranslation",
        "tracktranslation",
        "coursetranslation",
    ]

    Permission.objects.filter(content_type__model__in=models_to_remove).delete()
    ContentType.objects.filter(model__in=models_to_remove).delete()

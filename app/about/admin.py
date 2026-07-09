from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html
from project.admin_base import ModelAdmin
from unfold.admin import StackedInline, TabularInline
from unfold.sites import UnfoldAdminSite

from project.admin_helpers import UnhandledChangelistMixin, contact_link_icons
from project.phone_utils import normalize_phone
from .models import (
    AccountDeletionRequest,
    CompanyInfo,
    CompanyInfoTranslation,
    ContactMessage,
    FreeSession,
    HomePageContent,
    HomePageContentTranslation,
    HomePageFeature,
    HomePageFeatureTranslation,
    HomePageVideoPoint,
    HomePageVideoPointTranslation,
    LegalPage,
    LegalPageTranslation,
)


class CompanyInfoTranslationInline(TabularInline):
    model = CompanyInfoTranslation
    extra = 0
    tab = True


@admin.register(CompanyInfo)
class CompanyInfoAdmin(ModelAdmin):
    inlines = [CompanyInfoTranslationInline]
    list_display = ["name", "email", "phone", "whatsapp_number", "telegram_number", "logo_preview"]

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height:40px" />', obj.logo.url)
        return ""
    logo_preview.short_description = "Logo"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "telegram_number":
            formfield.label = "Telegram phone number"
            formfield.help_text = (
                "Use the phone number with country code, like +201095163117. "
                "This builds the public Telegram contact link."
            )
        return formfield


class HomePageContentTranslationInline(StackedInline):
    model = HomePageContentTranslation
    extra = 0
    tab = True
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


class HomePageFeatureTranslationInline(TabularInline):
    model = HomePageFeatureTranslation
    extra = 0
    tab = True
    fields = ("language", "title", "subtitle", "meta", "description")


class HomePageFeatureInline(StackedInline):
    model = HomePageFeature
    extra = 0
    tab = True
    fields = ("section", "icon_class", "image", "order", "is_active")
    show_change_link = True


class HomePageVideoPointTranslationInline(TabularInline):
    model = HomePageVideoPointTranslation
    extra = 0
    tab = True


class HomePageVideoPointInline(StackedInline):
    model = HomePageVideoPoint
    extra = 0
    tab = True
    fields = ("icon_class", "order", "is_active")
    show_change_link = True


@admin.register(HomePageContent)
class HomePageContentAdmin(ModelAdmin):
    list_display = (
        "id",
        "show_primary_features",
        "show_view_courses_button",
        "show_who_we_are_section",
        "show_video_section",
        "show_chat_section",
        "show_secondary_features",
        "show_teachers_section",
        "show_testimonials_section",
        "show_family_bundle_section",
        "show_family_bundle_comparison_section",
        "show_family_bundle_faq_section",
        "show_process_section",
        "show_free_session_section",
        "show_contact_section",
        "show_company_info_phone",
        "show_whatsapp_number",
        "show_telegram_number",
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
                        "show_view_courses_button",
                        "show_who_we_are_section",
                        "show_video_section",
                        "show_chat_section",
                        "show_secondary_features",
                        "show_teachers_section",
                        "show_testimonials_section",
                        "show_family_bundle_section",
                        "show_family_bundle_comparison_section",
                        "show_family_bundle_faq_section",
                        "show_process_section",
                        "show_free_session_section",
                        "show_contact_section",
                        "show_company_info_phone",
                        "show_whatsapp_number",
                        "show_telegram_number",
                    )
                },
            ),
    )

    def get_object(self, request, object_id, from_field=None):
        return HomePageContent.get_solo()

    def has_add_permission(self, request):
        if HomePageContent.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(HomePageFeature)
class HomePageFeatureAdmin(ModelAdmin):
    list_display = ("id", "section", "icon_class", "order", "is_active", "home_page")
    list_filter = ("section", "is_active")
    search_fields = ("icon_class",)
    ordering = ("section", "order", "id")
    inlines = [HomePageFeatureTranslationInline]


@admin.register(HomePageVideoPoint)
class HomePageVideoPointAdmin(ModelAdmin):
    list_display = ("id", "icon_class", "order", "is_active", "home_page")
    list_filter = ("is_active",)
    search_fields = ("icon_class",)
    ordering = ("order", "id")
    inlines = [HomePageVideoPointTranslationInline]


@admin.register(FreeSession)
class FreeSessionAdmin(UnhandledChangelistMixin, ModelAdmin):
    list_display = (
        "user_or_name",
        "user_phone",
        "contact_links",
        "handled",
        "requested_at",
        "marked_done_at",
    )
    list_filter = ("handled",)
    list_editable = ("handled",)
    search_fields = (
        "user__name",
        "user__username",
        "user__email",
        "user__phone",
        "name",
        "email",
        "phone",
    )
    ordering = ("handled", "-requested_at")
    readonly_fields = ("user", "name", "email", "phone", "message", "requested_at", "marked_done_at")

    def user_or_name(self, obj):
        if obj.user:
            return str(obj.user)
        return obj.name or "Anonymous"
    user_or_name.short_description = "User / Name"

    def user_phone(self, obj):
        return normalize_phone(obj.phone or (obj.user.phone if obj.user else "")) or "\u2014"
    user_phone.short_description = "Phone"

    def contact_links(self, obj):
        phone = obj.phone or (obj.user.phone if obj.user else "")
        email = obj.email or (obj.user.email if obj.user else "")
        return contact_link_icons(phone=phone, email=email)
    contact_links.short_description = "Contact"

    fieldsets = (
        (
            "User Info",
            {
                "fields": ("user", "name", "email", "phone", "message"),
            },
        ),
        (
            "Status",
            {
                "fields": ("handled", "requested_at", "marked_done_at"),
            },
        ),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(UnhandledChangelistMixin, ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone_number",
        "contact_links",
        "handled",
        "created_at",
    )
    list_filter = ("handled",)
    list_editable = ("handled",)
    search_fields = ("name", "email", "phone", "message")
    ordering = ("handled", "-created_at")
    readonly_fields = ("name", "email", "phone", "message", "created_at")
    actions = ["mark_as_handled", "mark_as_unhandled"]

    def contact_links(self, obj):
        return contact_link_icons(
            phone=obj.phone,
            email=obj.email,
        )

    contact_links.short_description = "Contact"

    def phone_number(self, obj):
        return normalize_phone(obj.phone) or "\u2014"

    phone_number.short_description = "Phone"
    phone_number.admin_order_field = "phone"

    @admin.action(description="Mark selected as handled")
    def mark_as_handled(self, request, queryset):
        updated = queryset.update(handled=True)
        self.message_user(request, f"{updated} message(s) marked as handled.")

    @admin.action(description="Mark selected as unhandled")
    def mark_as_unhandled(self, request, queryset):
        updated = queryset.update(handled=False)
        self.message_user(request, f"{updated} message(s) marked as unhandled.")

    fieldsets = (
        (
            "Message",
            {
                "fields": ("name", "email", "phone", "message"),
            },
        ),
        (
            "Status",
            {
                "fields": ("handled", "created_at"),
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


# =============================================================================
# Custom Admin Page for Fixture Upload
# =============================================================================


class FixtureUploadAdminSite(UnfoldAdminSite):
    site_header = "Fixture Upload"
    site_title = "Fixture Upload"
    index_template = "admin/fixture_upload.html"

    def index(self, request, extra_context=None):
        if request.method == "POST":
            return self._handle_upload(request)
        context = {
            **self.each_context(request),
            "title": "Upload Homepage Fixture",
            "available_fixtures": [
                {"name": "homepage_initial_data.json", "description": "Home Page Content, Features, and Translations"}
            ],
        }
        return render(request, self.index_template, context)

    def _handle_upload(self, request):
        import json

        fixture_file = request.FILES.get("fixture_file")
        if not fixture_file:
            context = {**self.each_context(request), "title": "Upload Homepage Fixture", "error": "No file uploaded",
                "available_fixtures": [{"name": "homepage_initial_data.json", "description": "Home Page Content, Features, and Translations"}],
            }
            return render(request, self.index_template, context)

        try:
            fixture_content = fixture_file.read().decode("utf-8").strip()
            if fixture_content.endswith("]"):
                fixture_content = fixture_content[:-1].rstrip().rstrip(",").rstrip()
            if not fixture_content.startswith("["):
                fixture_content = "[" + fixture_content + "]"
            fixture_data = json.loads(fixture_content)

            if not isinstance(fixture_data, list):
                context = {**self.each_context(request), "title": "Upload Homepage Fixture", "error": "Invalid fixture format. Expected a JSON array.",
                    "available_fixtures": [{"name": "homepage_initial_data.json", "description": "Home Page Content, Features, and Translations"}],
                }
                return render(request, self.index_template, context)

            results = load_fixture_data(fixture_data)
            success_msg = f"Successfully loaded fixture data: {results['created']} created, {results['updated']} updated."
            if results["errors"]:
                success_msg += f" Errors: {', '.join(results['errors'])}"

            context = {**self.each_context(request), "title": "Upload Homepage Fixture", "success": success_msg,
                "available_fixtures": [{"name": "homepage_initial_data.json", "description": "Home Page Content, Features, and Translations"}],
            }
            return render(request, self.index_template, context)

        except json.JSONDecodeError as e:
            context = {**self.each_context(request), "title": "Upload Homepage Fixture", "error": f"Invalid JSON: {str(e)}",
                "available_fixtures": [{"name": "homepage_initial_data.json", "description": "Home Page Content, Features, and Translations"}],
            }
            return render(request, self.index_template, context)
        except Exception as e:
            context = {**self.each_context(request), "title": "Upload Homepage Fixture", "error": f"Error loading fixture: {str(e)}",
                "available_fixtures": [{"name": "homepage_initial_data.json", "description": "Home Page Content, Features, and Translations"}],
            }
            return render(request, self.index_template, context)

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


fixture_upload_site = FixtureUploadAdminSite(name="fixture_upload")


def get_fixture_model_map():
    """Map fixture model names to actual Django models."""
    return {
        "about.homepagecontent": HomePageContent,
        "about.homepagecontenttranslation": HomePageContentTranslation,
        "about.homepagefeature": HomePageFeature,
        "about.homepagefeaturetranslation": HomePageFeatureTranslation,
        "about.homepagevideopoint": HomePageVideoPoint,
        "about.homepagevideopointtranslation": HomePageVideoPointTranslation,
    }


class LegalPageTranslationInline(TabularInline):
    model = LegalPageTranslation
    extra = 0
    tab = True


@admin.register(LegalPage)
class LegalPageAdmin(ModelAdmin):
    list_display = ("page_type", "is_active", "last_updated")
    list_filter = ("is_active", "page_type")
    search_fields = ("content",)
    inlines = [LegalPageTranslationInline]


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(ModelAdmin):
    list_display = (
        "user",
        "user_email",
        "status",
        "requested_at",
        "processed_at",
    )
    list_filter = ("status", "requested_at")
    search_fields = (
        "user__name",
        "user__username",
        "user__email",
        "reason",
    )
    readonly_fields = ("user", "requested_at", "processed_at")
    actions = ["mark_as_processed", "mark_as_rejected"]

    def user_email(self, obj):
        return obj.user.email or "—"

    user_email.short_description = "Email"

    @admin.action(description="Mark selected as processed")
    def mark_as_processed(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(status="processed", processed_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked as processed.")

    @admin.action(description="Mark selected as rejected")
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status="rejected", processed_at=None)
        self.message_user(request, f"{updated} request(s) marked as rejected.")

    fieldsets = (
        (
            "User Info",
            {
                "fields": ("user", "reason"),
            },
        ),
        (
            "Status",
            {
                "fields": ("status", "requested_at", "processed_at", "processed_by"),
            },
        ),
    )


def load_fixture_data(fixture_data):
    """
    Load fixture data into the database.

    - HomePageContent is treated as a singleton: replace the existing record if any.
    - HomePageContentTranslation is replaced by language (tied to the singleton).
    - HomePageFeature, HomePageVideoPoint are matched by (section, order) and
      replaced if a match exists; otherwise created (without hard-coding pk).
    - HomePageFeatureTranslation, HomePageVideoPointTranslation are matched by
      (parent, language) and replaced/created accordingly.
    - Foreign-key values in the fixture are resolved to real model instances,
      and a pk-remapping table tracks fixture-pk → real-pk so that child
      objects created later can point to newly-created parents.
    """
    model_map = get_fixture_model_map()
    results = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

    pk_map = {}

    SINGLETON_MODELS = {"about.homepagecontent"}
    SINGLETON_TRANSLATION_MODELS = {"about.homepagecontenttranslation"}
    EXTENDABLE_MODELS = {
        "about.homepagefeature",
        "about.homepagevideopoint",
    }
    EXTENDABLE_TRANSLATION_MODELS = {
        "about.homepagefeaturetranslation",
        "about.homepagevideopointtranslation",
    }

    def resolve_fk(model_class, fields):
        processed = {}
        for field_name, field_value in fields.items():
            if field_value is None:
                processed[field_name] = None
                continue
            fk_field = None
            for f in model_class._meta.get_fields():
                if f.name == field_name and hasattr(f, "remote_field") and f.remote_field is not None:
                    fk_field = f
                    break
            if fk_field is None:
                processed[field_name] = field_value
                continue
            if isinstance(field_value, (int, str)) and str(field_value).isdigit():
                related_model = fk_field.remote_field.model
                real_pk = pk_map.get((related_model.__name__, int(field_value)), int(field_value))
                try:
                    processed[field_name] = related_model.objects.get(pk=real_pk)
                except related_model.DoesNotExist:
                    results["errors"].append(
                        f"Referenced {related_model.__name__} pk={real_pk} not found for {model_class.__name__}.{field_name}"
                    )
                    processed[field_name] = None
            else:
                processed[field_name] = field_value
        return processed

    for entry in fixture_data:
        model_name = entry.get("model")
        fixture_pk = entry.get("pk")
        fields = entry.get("fields", {})

        if model_name not in model_map:
            results["errors"].append(f"Unknown model: {model_name}")
            continue

        model_class = model_map[model_name]

        try:
            processed = resolve_fk(model_class, fields)

            if model_name in SINGLETON_MODELS:
                existing = model_class.objects.first()
                if existing:
                    for attr, val in processed.items():
                        setattr(existing, attr, val)
                    existing.save(update_fields=[k for k in processed.keys() if k != "created_at"])
                    pk_map[(model_class.__name__, fixture_pk)] = existing.pk
                    results["updated"] += 1
                else:
                    obj = model_class.objects.create(**processed)
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["created"] += 1

            elif model_name in SINGLETON_TRANSLATION_MODELS:
                home_page = processed.get("home_page")
                language = processed.get("language")
                if home_page is None:
                    results["errors"].append(f"{model_name} (pk={fixture_pk}): missing home_page reference")
                    continue
                try:
                    obj = model_class.objects.get(home_page=home_page, language=language)
                    for attr, val in processed.items():
                        setattr(obj, attr, val)
                    obj.save()
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["updated"] += 1
                except model_class.DoesNotExist:
                    obj = model_class.objects.create(**processed)
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["created"] += 1

            elif model_name in EXTENDABLE_MODELS:
                section = processed.get("section")
                order = processed.get("order")
                home_page = processed.get("home_page")
                lookup = {"home_page": home_page, "order": order}
                if section is not None:
                    lookup["section"] = section
                try:
                    obj = model_class.objects.get(**lookup)
                    for attr, val in processed.items():
                        setattr(obj, attr, val)
                    obj.save()
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["updated"] += 1
                except model_class.DoesNotExist:
                    obj = model_class.objects.create(**processed)
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["created"] += 1
                except model_class.MultipleObjectsReturned:
                    objs = model_class.objects.filter(**lookup)
                    obj = objs.first()
                    for attr, val in processed.items():
                        setattr(obj, attr, val)
                    obj.save()
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["updated"] += 1
                    results["skipped"] += objs.count() - 1

            elif model_name in EXTENDABLE_TRANSLATION_MODELS:
                parent_field_name = None
                for f in model_class._meta.get_fields():
                    if hasattr(f, "remote_field") and f.remote_field and f.name not in ("home_page",):
                        if f.remote_field.model in [HomePageFeature, HomePageVideoPoint]:
                            parent_field_name = f.name
                            break
                if parent_field_name is None:
                    for f in model_class._meta.get_fields():
                        if hasattr(f, "remote_field") and f.remote_field and f.name != "home_page":
                            parent_field_name = f.name
                            break

                parent_obj = processed.get(parent_field_name)
                language = processed.get("language")
                if parent_obj is None:
                    results["errors"].append(f"{model_name} (pk={fixture_pk}): missing {parent_field_name} reference")
                    continue
                try:
                    obj = model_class.objects.get(**{parent_field_name: parent_obj, "language": language})
                    for attr, val in processed.items():
                        setattr(obj, attr, val)
                    obj.save()
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["updated"] += 1
                except model_class.DoesNotExist:
                    obj = model_class.objects.create(**processed)
                    pk_map[(model_class.__name__, fixture_pk)] = obj.pk
                    results["created"] += 1

            else:
                try:
                    obj = model_class.objects.get(pk=fixture_pk)
                    for attr, val in processed.items():
                        setattr(obj, attr, val)
                    obj.save()
                    results["updated"] += 1
                except model_class.DoesNotExist:
                    model_class.objects.create(pk=fixture_pk, **processed)
                    results["created"] += 1

        except Exception as e:
            results["errors"].append(f"Error with {model_name} (pk={fixture_pk}): {str(e)}")

    return results

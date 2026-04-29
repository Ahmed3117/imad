from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import format_html

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


# =============================================================================
# Custom Admin Page for Fixture Upload
# =============================================================================


class FixtureUploadAdminSite(admin.AdminSite):
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





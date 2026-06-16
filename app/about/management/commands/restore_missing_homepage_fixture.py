import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from about.models import (
    HomePageContent,
    HomePageContentTranslation,
    HomePageFeature,
    HomePageFeatureTranslation,
    HomePageVideoPoint,
    HomePageVideoPointTranslation,
)


class Command(BaseCommand):
    help = (
        "Create missing homepage rows from a fixture without deleting or "
        "overwriting existing production data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default="about/fixtures/homepage_initial_data.json",
            help="Path to the homepage fixture, relative to BASE_DIR or absolute.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write missing rows. Without this flag, only a dry-run is performed.",
        )

    def handle(self, *args, **options):
        fixture_path = self._resolve_fixture_path(options["fixture"])
        fixture_data = self._load_fixture(fixture_path)
        apply_changes = options["apply"]

        with transaction.atomic():
            stats = self._restore_missing(fixture_data, apply_changes=apply_changes)
            if not apply_changes:
                transaction.set_rollback(True)

        mode = "APPLIED" if apply_changes else "DRY-RUN"
        self.stdout.write(self.style.SUCCESS(f"{mode} homepage fixture restore"))
        for key in (
            "content_created",
            "content_skipped",
            "content_translations_created",
            "content_translations_skipped",
            "features_created",
            "features_skipped",
            "feature_translations_created",
            "feature_translations_skipped",
            "video_points_created",
            "video_points_skipped",
            "video_point_translations_created",
            "video_point_translations_skipped",
        ):
            self.stdout.write(f"{key}: {stats[key]}")

    def _resolve_fixture_path(self, fixture):
        path = Path(fixture)
        if path.is_absolute():
            return path

        from django.conf import settings

        return Path(settings.BASE_DIR) / path

    def _load_fixture(self, fixture_path):
        if not fixture_path.exists():
            raise CommandError(f"Fixture not found: {fixture_path}")

        with fixture_path.open(encoding="utf-8") as fixture_file:
            data = json.load(fixture_file)

        if not isinstance(data, list):
            raise CommandError("Fixture must be a JSON list.")

        return data

    def _restore_missing(self, fixture_data, apply_changes):
        stats = {
            "content_created": 0,
            "content_skipped": 0,
            "content_translations_created": 0,
            "content_translations_skipped": 0,
            "features_created": 0,
            "features_skipped": 0,
            "feature_translations_created": 0,
            "feature_translations_skipped": 0,
            "video_points_created": 0,
            "video_points_skipped": 0,
            "video_point_translations_created": 0,
            "video_point_translations_skipped": 0,
        }
        feature_map = {}
        video_point_map = {}

        home_page = HomePageContent.get_solo()
        for entry in fixture_data:
            if entry.get("model") != "about.homepagecontent":
                continue

            if home_page:
                stats["content_skipped"] += 1
            else:
                fields = self._clean_fields(entry.get("fields", {}), drop_auto=True)
                if apply_changes:
                    home_page = HomePageContent.objects.create(**fields)
                stats["content_created"] += 1
            break

        if home_page is None and not apply_changes:
            home_page = _DryRunObject(pk="new-homepage")

        if home_page is None:
            raise CommandError("Could not create or find HomePageContent.")

        for entry in fixture_data:
            model_name = entry.get("model")
            fields = entry.get("fields", {})
            fixture_pk = entry.get("pk")

            if model_name == "about.homepagecontenttranslation":
                language = fields.get("language")
                exists = (
                    not isinstance(home_page, _DryRunObject)
                    and HomePageContentTranslation.objects.filter(
                        home_page=home_page,
                        language=language,
                    ).exists()
                )
                if exists:
                    stats["content_translations_skipped"] += 1
                    continue

                create_fields = self._clean_fields(fields, drop_auto=True)
                create_fields["home_page"] = home_page
                if apply_changes:
                    HomePageContentTranslation.objects.create(**create_fields)
                stats["content_translations_created"] += 1

            elif model_name == "about.homepagefeature":
                key = (fields.get("section"), fields.get("order"))
                feature = None
                if not isinstance(home_page, _DryRunObject):
                    feature = HomePageFeature.objects.filter(
                        home_page=home_page,
                        section=key[0],
                        order=key[1],
                    ).order_by("id").first()

                if feature:
                    stats["features_skipped"] += 1
                else:
                    create_fields = self._clean_fields(fields, drop_auto=True)
                    create_fields["home_page"] = home_page
                    if apply_changes:
                        feature = HomePageFeature.objects.create(**create_fields)
                    else:
                        feature = _DryRunObject(pk=f"feature:{key[0]}:{key[1]}")
                    stats["features_created"] += 1
                feature_map[fixture_pk] = feature

            elif model_name == "about.homepagefeaturetranslation":
                feature = feature_map.get(fields.get("feature"))
                if feature is None:
                    raise CommandError(
                        f"Missing feature parent for fixture pk {fixture_pk}."
                    )

                language = fields.get("language")
                exists = (
                    not isinstance(feature, _DryRunObject)
                    and HomePageFeatureTranslation.objects.filter(
                        feature=feature,
                        language=language,
                    ).exists()
                )
                if exists:
                    stats["feature_translations_skipped"] += 1
                    continue

                create_fields = self._clean_fields(fields, drop_auto=True)
                create_fields["feature"] = feature
                if apply_changes:
                    HomePageFeatureTranslation.objects.create(**create_fields)
                stats["feature_translations_created"] += 1

            elif model_name == "about.homepagevideopoint":
                order = fields.get("order")
                video_point = None
                if not isinstance(home_page, _DryRunObject):
                    video_point = HomePageVideoPoint.objects.filter(
                        home_page=home_page,
                        order=order,
                    ).order_by("id").first()

                if video_point:
                    stats["video_points_skipped"] += 1
                else:
                    create_fields = self._clean_fields(fields, drop_auto=True)
                    create_fields["home_page"] = home_page
                    if apply_changes:
                        video_point = HomePageVideoPoint.objects.create(**create_fields)
                    else:
                        video_point = _DryRunObject(pk=f"video-point:{order}")
                    stats["video_points_created"] += 1
                video_point_map[fixture_pk] = video_point

            elif model_name == "about.homepagevideopointtranslation":
                video_point = video_point_map.get(fields.get("video_point"))
                if video_point is None:
                    raise CommandError(
                        f"Missing video point parent for fixture pk {fixture_pk}."
                    )

                language = fields.get("language")
                exists = (
                    not isinstance(video_point, _DryRunObject)
                    and HomePageVideoPointTranslation.objects.filter(
                        video_point=video_point,
                        language=language,
                    ).exists()
                )
                if exists:
                    stats["video_point_translations_skipped"] += 1
                    continue

                create_fields = self._clean_fields(fields, drop_auto=True)
                create_fields["video_point"] = video_point
                if apply_changes:
                    HomePageVideoPointTranslation.objects.create(**create_fields)
                stats["video_point_translations_created"] += 1

        return stats

    def _clean_fields(self, fields, drop_auto=False):
        cleaned = dict(fields)
        cleaned.pop("home_page", None)
        cleaned.pop("feature", None)
        cleaned.pop("video_point", None)
        if drop_auto:
            cleaned.pop("created_at", None)
            cleaned.pop("updated_at", None)
        return cleaned


class _DryRunObject:
    def __init__(self, pk):
        self.pk = pk

# Generated manually for homepage content models and translation fields

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("about", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomePageContent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hero_background_image",
                    models.ImageField(blank=True, null=True, upload_to="home/hero/"),
                ),
                (
                    "who_we_are_image",
                    models.ImageField(
                        blank=True, null=True, upload_to="home/who_we_are/"
                    ),
                ),
                (
                    "video_cover_image",
                    models.ImageField(blank=True, null=True, upload_to="home/video/"),
                ),
                (
                    "intro_video",
                    models.FileField(blank=True, null=True, upload_to="home/video/"),
                ),
                (
                    "chat_image",
                    models.ImageField(blank=True, null=True, upload_to="home/chat/"),
                ),
                (
                    "contact_illustration",
                    models.ImageField(blank=True, null=True, upload_to="home/contact/"),
                ),
                (
                    "hero_primary_button_url",
                    models.CharField(default="/courses/", max_length=255),
                ),
                (
                    "who_we_are_button_url",
                    models.CharField(default="/courses/", max_length=255),
                ),
                (
                    "footer_cta_url",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "facebook_url",
                    models.URLField(blank=True, max_length=500, null=True),
                ),
                ("show_primary_features", models.BooleanField(default=True)),
                ("show_who_we_are_section", models.BooleanField(default=True)),
                ("show_video_section", models.BooleanField(default=True)),
                ("show_chat_section", models.BooleanField(default=True)),
                ("show_secondary_features", models.BooleanField(default=True)),
                ("show_teachers_section", models.BooleanField(default=True)),
                ("show_contact_section", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Home Page Content",
                "verbose_name_plural": "Home Page Content",
            },
        ),
        migrations.CreateModel(
            name="HomePageContentTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("language", models.CharField(max_length=10)),
                ("hero_badge", models.CharField(blank=True, max_length=100, null=True)),
                ("hero_title", models.CharField(blank=True, max_length=255, null=True)),
                ("hero_description", models.TextField(blank=True, null=True)),
                (
                    "hero_primary_button_text",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "hero_side_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("hero_side_description", models.TextField(blank=True, null=True)),
                (
                    "primary_features_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "primary_features_description",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "primary_features_empty_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "who_we_are_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("who_we_are_lead", models.TextField(blank=True, null=True)),
                ("who_we_are_description", models.TextField(blank=True, null=True)),
                (
                    "who_we_are_button_text",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "video_section_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("video_section_description", models.TextField(blank=True, null=True)),
                (
                    "video_point_fallback",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "chat_section_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("chat_section_description_1", models.TextField(blank=True, null=True)),
                ("chat_section_description_2", models.TextField(blank=True, null=True)),
                (
                    "chat_button_text",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "secondary_features_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "secondary_features_description",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "secondary_features_empty_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "teachers_section_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("teachers_section_subtitle", models.TextField(blank=True, null=True)),
                (
                    "contact_section_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "contact_section_description",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "contact_info_title",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("contact_info_description", models.TextField(blank=True, null=True)),
                (
                    "facebook_label",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("footer_description", models.TextField(blank=True, null=True)),
                (
                    "footer_cta_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "footer_created_by_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "footer_copyright_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "home_page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="about.homepagecontent",
                    ),
                ),
            ],
            options={
                "verbose_name": "Home Page Translation",
                "verbose_name_plural": "Home Page Translations",
                "unique_together": {("home_page", "language")},
            },
        ),
        migrations.CreateModel(
            name="HomePageFeature",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "section",
                    models.CharField(
                        choices=[
                            ("primary", "Primary Features"),
                            ("secondary", "Secondary Features"),
                        ],
                        max_length=20,
                    ),
                ),
                ("icon_class", models.CharField(default="fas fa-star", max_length=100)),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="home/features/"
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "home_page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="features",
                        to="about.homepagecontent",
                    ),
                ),
            ],
            options={
                "verbose_name": "Home Page Feature",
                "verbose_name_plural": "Home Page Features",
                "ordering": ["section", "order", "id"],
            },
        ),
        migrations.CreateModel(
            name="HomePageFeatureTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("language", models.CharField(max_length=10)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "feature",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="about.homepagefeature",
                    ),
                ),
            ],
            options={
                "verbose_name": "Home Page Feature Translation",
                "verbose_name_plural": "Home Page Feature Translations",
                "unique_together": {("feature", "language")},
            },
        ),
        migrations.CreateModel(
            name="HomePageVideoPoint",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "icon_class",
                    models.CharField(default="fas fa-check-circle", max_length=100),
                ),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "home_page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="video_points",
                        to="about.homepagecontent",
                    ),
                ),
            ],
            options={
                "verbose_name": "Home Page Video Point",
                "verbose_name_plural": "Home Page Video Points",
                "ordering": ["order", "id"],
            },
        ),
        migrations.CreateModel(
            name="HomePageVideoPointTranslation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("language", models.CharField(max_length=10)),
                ("text", models.CharField(max_length=255)),
                (
                    "video_point",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="about.homepagevideopoint",
                    ),
                ),
            ],
            options={
                "verbose_name": "Home Page Video Point Translation",
                "verbose_name_plural": "Home Page Video Point Translations",
                "unique_together": {("video_point", "language")},
            },
        ),
    ]

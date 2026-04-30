from django.conf import settings
from django.db import models


class CompanyInfo(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name


class CompanyInfoTranslation(models.Model):
    company_info = models.ForeignKey(
        CompanyInfo, on_delete=models.CASCADE, related_name="translations"
    )
    language = models.CharField(max_length=10)  # e.g. en, ar
    translated_name = models.CharField(max_length=255)
    translated_description = models.TextField()

    class Meta:
        unique_together = ("company_info", "language")
        default_permissions = ()

    def __str__(self):
        return f"{self.company_info.name} - {self.language}"


class HomePageContent(models.Model):
    hero_background_image = models.ImageField(
        upload_to="home/hero/", blank=True, null=True
    )
    who_we_are_image = models.ImageField(
        upload_to="home/who_we_are/", blank=True, null=True
    )
    video_cover_image = models.ImageField(
        upload_to="home/video/", blank=True, null=True
    )
    intro_video = models.FileField(upload_to="home/video/", blank=True, null=True)
    chat_image = models.ImageField(upload_to="home/chat/", blank=True, null=True)
    contact_illustration = models.ImageField(
        upload_to="home/contact/", blank=True, null=True
    )

    hero_primary_button_url = models.CharField(max_length=255, default="/courses/")
    who_we_are_button_url = models.CharField(max_length=255, default="/courses/")
    footer_cta_url = models.CharField(max_length=255, blank=True, null=True)
    facebook_url = models.URLField(max_length=500, blank=True, null=True)

    show_primary_features = models.BooleanField(default=True)
    show_who_we_are_section = models.BooleanField(default=True)
    show_video_section = models.BooleanField(default=True)
    show_chat_section = models.BooleanField(default=True)
    show_secondary_features = models.BooleanField(default=True)
    show_teachers_section = models.BooleanField(default=True)
    show_contact_section = models.BooleanField(default=True)
    show_company_info_phone = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Home Page Content"
        verbose_name_plural = "Home Page Content"

    def __str__(self):
        return "Home Page Content"

    @classmethod
    def get_solo(cls):
        return cls.objects.order_by("id").first()


class HomePageContentTranslation(models.Model):
    home_page = models.ForeignKey(
        HomePageContent, on_delete=models.CASCADE, related_name="translations"
    )
    language = models.CharField(max_length=10)

    hero_badge = models.CharField(max_length=255, blank=True, null=True)
    hero_title = models.CharField(max_length=255, blank=True, null=True)
    hero_description = models.TextField(blank=True, null=True)
    hero_primary_button_text = models.CharField(max_length=100, blank=True, null=True)
    hero_side_title = models.CharField(max_length=255, blank=True, null=True)
    hero_side_description = models.TextField(blank=True, null=True)
    hero_trust_badge_1 = models.CharField(max_length=255, blank=True, null=True)
    hero_trust_badge_2 = models.CharField(max_length=255, blank=True, null=True)
    hero_trust_badge_3 = models.CharField(max_length=255, blank=True, null=True)
    hero_trust_badge_4 = models.CharField(max_length=255, blank=True, null=True)
    hero_pricing_note = models.CharField(max_length=255, blank=True, null=True)

    primary_features_title = models.CharField(max_length=255, blank=True, null=True)
    primary_features_description = models.TextField(blank=True, null=True)
    primary_features_empty_text = models.CharField(
        max_length=255, blank=True, null=True
    )

    who_we_are_title = models.CharField(max_length=255, blank=True, null=True)
    who_we_are_lead = models.TextField(blank=True, null=True)
    who_we_are_description = models.TextField(blank=True, null=True)
    who_we_are_button_text = models.CharField(max_length=100, blank=True, null=True)

    video_section_title = models.CharField(max_length=255, blank=True, null=True)
    video_section_description = models.TextField(blank=True, null=True)
    video_point_fallback = models.CharField(max_length=255, blank=True, null=True)

    chat_section_title = models.CharField(max_length=255, blank=True, null=True)
    chat_section_description_1 = models.TextField(blank=True, null=True)
    chat_section_description_2 = models.TextField(blank=True, null=True)
    chat_button_text = models.CharField(max_length=100, blank=True, null=True)

    secondary_features_title = models.CharField(max_length=255, blank=True, null=True)
    secondary_features_description = models.TextField(blank=True, null=True)
    secondary_features_empty_text = models.CharField(
        max_length=255, blank=True, null=True
    )

    teachers_section_title = models.CharField(max_length=255, blank=True, null=True)
    teachers_section_subtitle = models.TextField(blank=True, null=True)

    testimonials_section_title = models.CharField(max_length=255, blank=True, null=True)
    testimonials_section_subtitle = models.TextField(blank=True, null=True)

    process_section_title = models.CharField(max_length=255, blank=True, null=True)
    process_section_description = models.TextField(blank=True, null=True)

    free_session_section_badge = models.CharField(max_length=255, blank=True, null=True)
    free_session_section_title = models.CharField(max_length=255, blank=True, null=True)
    free_session_section_description = models.TextField(blank=True, null=True)
    free_session_privacy_note = models.TextField(blank=True, null=True)

    family_bundle_section_badge = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_section_title = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_section_description = models.TextField(blank=True, null=True)
    family_bundle_section_pricing_note_1 = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_section_pricing_note_2 = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_section_pricing_note_3 = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_section_pricing_note_4 = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_plans_title = models.CharField(max_length=255, blank=True, null=True)
    family_bundle_plans_description = models.TextField(blank=True, null=True)
    family_bundle_comparison_title = models.CharField(
        max_length=255, blank=True, null=True
    )
    family_bundle_comparison_description = models.TextField(blank=True, null=True)
    family_bundle_faq_title = models.CharField(max_length=255, blank=True, null=True)
    family_bundle_faq_description = models.TextField(blank=True, null=True)
    family_bundle_cta_title = models.CharField(max_length=255, blank=True, null=True)
    family_bundle_cta_description = models.TextField(blank=True, null=True)
    family_bundle_cta_button_text = models.CharField(
        max_length=255, blank=True, null=True
    )

    contact_section_title = models.CharField(max_length=255, blank=True, null=True)
    contact_section_description = models.TextField(blank=True, null=True)
    contact_info_title = models.CharField(max_length=255, blank=True, null=True)
    contact_info_description = models.TextField(blank=True, null=True)
    facebook_label = models.CharField(max_length=255, blank=True, null=True)

    footer_description = models.TextField(blank=True, null=True)
    footer_cta_text = models.CharField(max_length=255, blank=True, null=True)
    footer_created_by_text = models.CharField(max_length=255, blank=True, null=True)
    footer_copyright_text = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("home_page", "language")
        verbose_name = "Home Page Translation"
        verbose_name_plural = "Home Page Translations"

    def __str__(self):
        return f"Home Page - {self.language}"


class HomePageFeature(models.Model):
    SECTION_CHOICES = (
        ("primary", "Primary Features"),
        ("secondary", "Secondary Features"),
        ("testimonials", "Testimonials"),
        ("process", "Process Steps"),
        ("family_bundle_plans", "Family Bundle Plans"),
        ("family_bundle_comparison", "Family Bundle Comparison"),
        ("family_bundle_testimonials", "Family Bundle Testimonials"),
        ("family_bundle_faq", "Family Bundle FAQ"),
    )

    home_page = models.ForeignKey(
        HomePageContent, on_delete=models.CASCADE, related_name="features"
    )
    section = models.CharField(max_length=40, choices=SECTION_CHOICES)
    icon_class = models.CharField(max_length=100, default="fas fa-star")
    image = models.ImageField(upload_to="home/features/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "order", "id"]
        verbose_name = "Home Page Feature"
        verbose_name_plural = "Home Page Features"

    def __str__(self):
        return f"{self.get_section_display()} #{self.order}"


class HomePageFeatureTranslation(models.Model):
    feature = models.ForeignKey(
        HomePageFeature, on_delete=models.CASCADE, related_name="translations"
    )
    language = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    meta = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("feature", "language")
        verbose_name = "Home Page Feature Translation"
        verbose_name_plural = "Home Page Feature Translations"

    def __str__(self):
        return f"{self.title} - {self.language}"


class HomePageVideoPoint(models.Model):
    home_page = models.ForeignKey(
        HomePageContent, on_delete=models.CASCADE, related_name="video_points"
    )
    icon_class = models.CharField(max_length=100, default="fas fa-check-circle")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Home Page Video Point"
        verbose_name_plural = "Home Page Video Points"

    def __str__(self):
        return f"Video Point #{self.order}"


class HomePageVideoPointTranslation(models.Model):
    video_point = models.ForeignKey(
        HomePageVideoPoint, on_delete=models.CASCADE, related_name="translations"
    )
    language = models.CharField(max_length=10)
    text = models.CharField(max_length=255)

    class Meta:
        unique_together = ("video_point", "language")
        verbose_name = "Home Page Video Point Translation"
        verbose_name_plural = "Home Page Video Point Translations"

    def __str__(self):
        return f"{self.text} - {self.language}"


class FreeSession(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("done", "Done"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="free_session",
    )
    phone = models.CharField(max_length=30, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    marked_done_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Free Session Request"
        verbose_name_plural = "Free Session Requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.user} – {self.get_status_display()}"

# contact/models.py
from django.db import models
from ckeditor.fields import RichTextField

class CompanyInfo(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    phone = models.CharField(max_length=30)
    freemeet_phone = models.CharField(max_length=30)
    email = models.EmailField()
    video = models.CharField(max_length=500)
    
    def __str__(self):
        return self.name

class CompanyDescription(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    order = models.PositiveIntegerField()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']

class SocialAccount(models.Model):
    country_code = models.CharField(max_length=2)  # ISO 3166-1 alpha-2
    platform_name = models.CharField(max_length=50)  # e.g., Instagram, Facebook, etc.
    icon = models.ImageField(upload_to='social_icons/')  # Upload icons for each platform
    url = models.URLField()

    def __str__(self):
        return f"{self.platform_name} - {self.country_code}"

class Tech(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='techs/', default='defaults/software.gif')
    color = models.CharField(max_length=50 , default='blue')
    def __str__(self):
        return self.name

class TechUsage(models.Model):
    name = models.CharField(max_length=100)
    tech = models.ForeignKey(Tech, on_delete=models.CASCADE, related_name='usages')

    def __str__(self):
        return f"{self.name} (Tech: {self.tech.name})"
    
    
class Policy(models.Model):
    POLICY_TYPES = [
        ('terms', 'Terms and Conditions'),
        ('refund', 'Refund Policy'),
        ('exchange', 'Exchange Policy'),
        ('privacy', 'Privacy Policy'),
    ]

    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES, unique=True)
    content = RichTextField()  # Use RichTextField instead of TextField
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_policy_type_display()


class FinalProject(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    code_url = models.CharField(max_length=255, blank=True, null=True)
    preview_url = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='final_projects/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

#------------------------translation models-----------------------------------#

class CompanyInfoTranslation(models.Model):
    company_info = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=255)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('company_info', 'language')

    def __str__(self):
        return f"{self.company_info.name} - {self.language}"

class CompanyDescriptionTranslation(models.Model):
    company_description = models.ForeignKey(CompanyDescription, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_title = models.CharField(max_length=255)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('company_description', 'language')

    def __str__(self):
        return f"{self.company_description.title} - {self.language}"

class TechTranslation(models.Model):
    tech = models.ForeignKey(Tech, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('tech', 'language')

    def __str__(self):
        return f"{self.tech.name} - {self.language}"

class TechUsageTranslation(models.Model):
    tech_usage = models.ForeignKey(TechUsage, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('tech_usage', 'language')

    def __str__(self):
        return f"{self.tech_usage.name} - {self.language}"

class PolicyTranslation(models.Model):
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_content = RichTextField()  # Translated content

    class Meta:
        unique_together = ('policy', 'language')  # Ensure one translation per language per policy

    def __str__(self):
        return f"{self.policy.get_policy_type_display()} - {self.language}"


class FinalProjectTranslation(models.Model):
    final_project = models.ForeignKey(FinalProject, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_title = models.CharField(max_length=255)
    translated_description = models.TextField()




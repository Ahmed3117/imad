# contact/models.py
from django.db import models
from ckeditor.fields import RichTextField

class CompanyInfo(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    phone = models.CharField(max_length=30)
    # freemeet_phone = models.CharField(max_length=30)
    email = models.EmailField()
    video = models.CharField(max_length=500)
    
    def __str__(self):
        return self.name


#------------------------translation models-----------------------------------#

class CompanyInfoTranslation(models.Model):
    company_info = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=10)  # e.g., 'en', 'ar'
    translated_name = models.CharField(max_length=255)
    translated_description = models.TextField()

    class Meta:
        unique_together = ('company_info', 'language')
        default_permissions = ()

    def __str__(self):
        return f"{self.company_info.name} - {self.language}"





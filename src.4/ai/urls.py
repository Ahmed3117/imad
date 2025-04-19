from django.urls import path
from . import views

urlpatterns = [
    path('generate-mcqs/', views.MCQGeneratorView.as_view(), name='generate-mcqs'),
    path('generate-image-mcqs/', views.ImageMCQExtractorView.as_view(), name='generate-image-mcqs'),
    path('generate-national-id/', views.EgyptianIDExtractorView.as_view(), name='generate-national-id'),
]

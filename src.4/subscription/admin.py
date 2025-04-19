from django.contrib import admin
from .models import CourseSubscription,LessonSubscription
# Register your models here.
admin.site.register(CourseSubscription)
admin.site.register(LessonSubscription)


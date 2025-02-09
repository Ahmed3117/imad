from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CartLevel, CartTrack, CartCourse

@admin.register(CartLevel)
class CartLevelAdmin(admin.ModelAdmin):
    list_display = ('student', 'level', 'date_added')
    list_filter = ('student', 'date_added')
    search_fields = ('student__username', 'level__name')

@admin.register(CartTrack)
class CartTrackAdmin(admin.ModelAdmin):
    list_display = ('student', 'track', 'date_added')
    list_filter = ('student', 'date_added')
    search_fields = ('student__username', 'track__name')

@admin.register(CartCourse)
class CartCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date_added')
    list_filter = ('student', 'date_added')
    search_fields = ('student__username', 'course__name')
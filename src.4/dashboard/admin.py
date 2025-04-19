from django.contrib import admin
from django.contrib.admin.models import LogEntry
from .models import RequestLog
# Register your models here.
admin.site.register(LogEntry)
admin.site.register(RequestLog)
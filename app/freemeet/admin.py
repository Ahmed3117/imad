from django.urls import path
from django.utils.html import format_html
from django.contrib import admin

from freemeet.models import FreeMeet


class FreeMeetAdmin(admin.ModelAdmin):
    list_display = ('student', 'phone_number', 'respond_status', 'meet_url', 'created_at', 'whatsapp_button', 'email_button')
    list_filter = ('respond_status',)
    search_fields = ('student__username', 'phone_number')

    def whatsapp_button(self, obj):
        if obj.respond_status == "pending" and obj.meet_url and obj.phone_number:
            return format_html(
                '<a class="button" href="{}">Send WhatsApp</a>',
                f"/freemeet/send_whatsapp/{obj.id}/"
            )
        return "N/A"
    whatsapp_button.short_description = "WhatsApp Link"
    whatsapp_button.allow_tags = True

    def email_button(self, obj):
        if obj.respond_status == "pending" and obj.meet_url and obj.student_email:
            return format_html(
                '<a class="button" href="{}">Send Email</a>',
                f"/freemeet/send_meeting_email/{obj.id}/"
            )
        return "N/A"
    email_button.short_description = "Email Link"
    email_button.allow_tags = True


admin.site.register(FreeMeet, FreeMeetAdmin)

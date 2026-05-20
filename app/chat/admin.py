from django.contrib import admin

from chat.models import Message, Room


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("sender", "is_agent", "text", "timestamp")
    readonly_fields = ("timestamp",)
    autocomplete_fields = ("sender",)
    show_change_link = True


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "status",
        "agent",
        "admin_unread_count",
        "user_unread_count",
        "created_at",
    )
    list_filter = ("status", "created_at", "agent")
    search_fields = ("code", "agent__username", "agent__name", "messages__text")
    autocomplete_fields = ("agent",)
    readonly_fields = ("code", "created_at", "admin_unread_count", "user_unread_count")
    date_hierarchy = "created_at"
    inlines = (MessageInline,)
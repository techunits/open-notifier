from django.contrib import admin
from .models import Configuration, NotificationLog


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "notification_type",
        "metadata",
        "is_enabled",
        "created_on",
        "modified_on",
    )


admin.site.register(Configuration, ConfigurationAdmin)


class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_ref", "status", "created_on")
    list_filter = ("status",)


admin.site.register(NotificationLog, NotificationLogAdmin)

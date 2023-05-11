from django.contrib import admin
from .models import Template


class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "name",
        "ref",
        "addon_data",
        "is_enabled",
        "created_on",
        "modified_on",
    )


admin.site.register(Template, TemplateAdmin)

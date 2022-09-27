from django.contrib import admin
from .models import Template

class TemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ref', 'is_enabled', 'created_on', 'modified_on')
    
admin.site.register(Template, TemplateAdmin)
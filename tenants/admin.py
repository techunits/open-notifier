from django.contrib import admin
from .models import Tenant

class TenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_enabled', 'created_on', 'modified_on')
    
admin.site.register(Tenant, TenantAdmin)
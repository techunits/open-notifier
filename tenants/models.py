from django.db import models
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField

class Tenant(models.Model):
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    modified_on = UnixTimeStampField(use_numeric=True, auto_now=True, default=timezone.now)
    created_by = models.UUIDField(null=True, blank=True)
    modified_by = models.UUIDField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'tenants'
    

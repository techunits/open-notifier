from email.policy import default
from random import choices
from re import template
from django.db import models
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField
from django.template import Template as DjangoTemplate, Context
from tenants.models import Tenant

NOTIFICATION_TYPE_CHOICES = [
    ("EMAIL", "EMAIL")
]


NOTIFICATION_STATUS_CHOICES = [
    ("QUEUED", "QUEUED"),
    ("SUCCESS", "SUCCESS"),
    ("FAILED", "FAILED")
]


class Configuration(models.Model):
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    tenant = models.ForeignKey(Tenant, related_name='configurations', on_delete=models.CASCADE)
    config_type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default="EMAIL")
    provider = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField()
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    modified_on = UnixTimeStampField(use_numeric=True, auto_now=True, default=timezone.now)
    created_by = models.UUIDField(null=True, blank=True)
    modified_by = models.UUIDField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.config_type} configuration'
    
    class Meta:
        db_table = 'configurations'
    

class NotificationLog(models.Model):
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    tenant = models.ForeignKey(Tenant, related_name='notification_logs', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default="EMAIL")
    status = models.CharField(max_length=100, choices=NOTIFICATION_STATUS_CHOICES, default="QUEUED")
    metadata = models.JSONField()
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    modified_on = UnixTimeStampField(use_numeric=True, auto_now=True, default=timezone.now)
    created_by = models.UUIDField(null=True, blank=True)
    modified_by = models.UUIDField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.notification_type}-{self.status}'
    
    class Meta:
        db_table = 'notification_logs'

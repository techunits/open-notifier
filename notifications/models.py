from email.policy import default
from random import choices
from re import template
from django.db import models
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField
from django.template import Template as DjangoTemplate, Context

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
    config_type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default="EMAIL")
    metadata = models.JSONField()
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    modified_on = UnixTimeStampField(use_numeric=True, auto_now=True, default=timezone.now)
    created_by = models.UUIDField()
    modified_by = models.UUIDField()
    
    def __str__(self):
        return f'{self.type} configuration'
    
    class Meta:
        db_table = 'configurations'
    

class NotificationLog(models.Model):
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    notification_type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default="EMAIL")
    status = models.CharField(max_length=100, choices=NOTIFICATION_STATUS_CHOICES, default="QUEUED")
    metadata = models.JSONField()
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    created_by = models.UUIDField()
    
    def __str__(self):
        return f'{self.entity_type}-{self.status}'
    
    class Meta:
        db_table = 'notification_logs'
    


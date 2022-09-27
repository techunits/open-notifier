from email.policy import default
from random import choices
from re import template
from django.db import models
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField
from django.template import Template as DjangoTemplate, Context

CONFIG_TYPE_CHOICES = [
    ("EMAIL", "EMAIL")
]

class Configuration(models.Model):
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    type = models.CharField(max_length=100, choices=CONFIG_TYPE_CHOICES, default="EMAIL")
    metadata = models.JSONField()
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    modified_on = UnixTimeStampField(use_numeric=True, auto_now=True, default=timezone.now)
    created_by = models.UUIDField()
    modified_by = models.UUIDField()
    
    def __str__(self):
        return self.slug
    
    class Meta:
        db_table = 'configurations'
    
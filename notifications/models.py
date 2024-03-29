from django.db import models
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField
from tenants.models import Tenant

NOTIFICATION_STATUS_CHOICES = [
    ("QUEUED", "QUEUED"),
    ("PROCESSING", "PROCESSING"),
    ("SUCCESS", "SUCCESS"),
    ("FAILED", "FAILED"),
]

NOTIFICATION_TYPE_CHOICES = [
    ("EMAIL", "EMAIL"),
    ("WHATSAPP", "WHATSAPP"),
    ("SMS", "SMS"),
]

PROVIDER_STATUS_CHOICES = [
    ("LOCAL_EMAIL", "LOCAL_EMAIL"),
    ("INTERAKT", "INTERAKT"),
]


class Configuration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, related_name="configurations", on_delete=models.CASCADE
    )
    notification_type = models.CharField(
        max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default="EMAIL"
    )
    provider = models.CharField(
        max_length=100, default="LOCAL_EMAIL", choices=PROVIDER_STATUS_CHOICES
    )
    metadata = models.JSONField()
    is_default = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(
        use_numeric=True, auto_now_add=True, default=timezone.now
    )
    modified_on = UnixTimeStampField(
        use_numeric=True, auto_now=True, default=timezone.now
    )
    created_by = models.UUIDField(null=True, blank=True)
    modified_by = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_type} - {self.provider}"

    class Meta:
        db_table = "configurations"


class NotificationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification_ref = models.ForeignKey(
        Configuration, related_name="notification_logs", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=100, choices=NOTIFICATION_STATUS_CHOICES, default="QUEUED"
    )
    metadata = models.JSONField()
    created_on = UnixTimeStampField(
        use_numeric=True, auto_now_add=True, default=timezone.now
    )
    modified_on = UnixTimeStampField(
        use_numeric=True, auto_now=True, default=timezone.now
    )
    created_by = models.UUIDField(null=True, blank=True)
    modified_by = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_ref}: {self.status}"

    class Meta:
        db_table = "notification_logs"

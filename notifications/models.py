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

# Provider choices are auto-populated at startup by scanning
# notifications/integrations/ (each package with a sender.py). Drop in a new
# provider package and it registers automatically after a restart — no model
# edit or migration needed. `choices` is intentionally NOT set on the model
# fields (that would bake the list into a migration); provider values are
# validated at the API layer instead.
from notifications.integrations import discover_provider_choices

PROVIDER_STATUS_CHOICES = discover_provider_choices()


class Configuration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, related_name="configurations", on_delete=models.CASCADE
    )
    notification_type = models.CharField(
        max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default="EMAIL"
    )
    provider = models.CharField(max_length=100, default="SMTP_EMAIL")
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


class IntegrationState(models.Model):
    """Enable/disable state for a discovered provider integration.

    Providers are discovered from the filesystem; this row records whether a
    given provider may deliver notifications. A provider with **no** row (or an
    ``is_enabled=False`` row) is treated as **disabled** — new providers are
    therefore disabled by default until an admin enables them.
    """

    provider = models.CharField(max_length=100, unique=True)
    is_enabled = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integration_states"

    def __str__(self):
        return f"{self.provider}: {'enabled' if self.is_enabled else 'disabled'}"

    @classmethod
    def enabled_providers(cls):
        return set(
            cls.objects.filter(is_enabled=True).values_list("provider", flat=True)
        )

    @classmethod
    def is_provider_enabled(cls, provider):
        return cls.objects.filter(provider=provider, is_enabled=True).exists()

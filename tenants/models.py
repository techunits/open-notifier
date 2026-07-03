from django.db import models
import hashlib
import secrets
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
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
        return self.name

    class Meta:
        db_table = "tenants"


class TenantApiKey(models.Model):
    """A tenant-scoped API key used to authenticate the public client API.

    The raw key is shown to the user exactly once (at creation); only a
    quantum-resistant **SHA3-512** hash is stored, so it can never be
    recovered. ``last_six`` keeps the trailing characters for identification.
    """

    KEY_PREFIX = "enk_"
    KEY_LENGTH = 256  # total characters of a raw key (prefix + random filler)
    # Allowed expiry windows, in days (None == never expire).
    EXPIRY_DAYS = [7, 30, 90, 120, 365]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, related_name="api_keys", on_delete=models.CASCADE
    )
    label = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=128, unique=True, db_index=True)
    last_six = models.CharField(max_length=6)
    expires_on = models.DateTimeField(null=True, blank=True)  # null == never
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    last_used_on = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "tenant_api_keys"

    def __str__(self):
        return f"{self.tenant.name}: {self.label} (…{self.last_six})"

    @staticmethod
    def hash_key(raw_key):
        """SHA3-512 (quantum-resistant) hex digest of a raw key.

        API keys are high-entropy random tokens, so a fast unsalted
        cryptographic hash is appropriate and lets us look keys up directly.
        """
        return hashlib.sha3_512(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def generate_raw_key(cls):
        # Exactly KEY_LENGTH characters: the prefix plus URL-safe random filler.
        random_len = cls.KEY_LENGTH - len(cls.KEY_PREFIX)
        filler = secrets.token_urlsafe(random_len)  # yields more than enough chars
        return cls.KEY_PREFIX + filler[:random_len]

    @property
    def is_expired(self):
        return self.expires_on is not None and self.expires_on <= timezone.now()

    @property
    def is_valid(self):
        return self.is_active and not self.is_deleted and not self.is_expired

from django.contrib.auth.models import User
from django.db import models

from tenants.models import Tenant


class Membership(models.Model):
    """Binds a Django auth user to a webmaster-console role and, for the
    tenant-scoped roles, the set of tenants they may act on.

    PLATFORM_ADMIN ignores ``tenants`` (full access to everything). A Django
    superuser is treated as PLATFORM_ADMIN even without a Membership row.
    """

    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    CONFIG_ADMIN = "CONFIG_ADMIN"
    DESIGN_ADMIN = "DESIGN_ADMIN"
    ROLE_CHOICES = [
        (PLATFORM_ADMIN, "Platform Admin"),
        (TENANT_ADMIN, "Tenant Admin"),
        (CONFIG_ADMIN, "Config Admin"),
        (DESIGN_ADMIN, "Design Admin"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="membership"
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    tenants = models.ManyToManyField(
        Tenant, blank=True, related_name="memberships"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "en_console_memberships"

    def __str__(self):
        return f"{self.user.username} ({self.role})"

"""Role model for the webmaster console.

Four roles, resolved from a user's :class:`~en_console.models.Membership`
(a Django superuser is always PLATFORM_ADMIN):

* ``PLATFORM_ADMIN`` – full access to everything, all tenants.
* ``TENANT_ADMIN``   – full access, restricted to its associated tenants
  (cannot create/delete tenants; manages only CONFIG/DESIGN users in its tenants).
* ``CONFIG_ADMIN``   – configurations, integrations and templates (CRUD) plus
  notification-log viewing, for its associated tenants.
* ``DESIGN_ADMIN``   – EMAIL templates (CRUD) for its associated tenants; no dashboard.

Everything here is capability + tenant-scope logic shared by the API views and
the page views. The API layer is the real security boundary; the sidebar/UI
gating mirrors it for usability only.
"""
from .models import Membership

PLATFORM_ADMIN = Membership.PLATFORM_ADMIN
TENANT_ADMIN = Membership.TENANT_ADMIN
CONFIG_ADMIN = Membership.CONFIG_ADMIN
DESIGN_ADMIN = Membership.DESIGN_ADMIN

ALL_ROLES = [PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN, DESIGN_ADMIN]

# Roles a TENANT_ADMIN is allowed to grant to the users it manages.
TENANT_GRANTABLE_ROLES = {CONFIG_ADMIN, DESIGN_ADMIN}


def resolve_role(user):
    """Return the effective role string for ``user`` or ``None`` (no access)."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return PLATFORM_ADMIN
    try:
        return user.membership.role
    except (Membership.DoesNotExist, AttributeError):
        return None


def accessible_tenant_ids(user):
    """Tenant scope for ``user``.

    Returns ``None`` for unrestricted access (PLATFORM_ADMIN), otherwise a set
    of tenant UUIDs the user is associated with (possibly empty).
    """
    if resolve_role(user) == PLATFORM_ADMIN:
        return None
    try:
        membership = user.membership
    except (Membership.DoesNotExist, AttributeError):
        return set()
    return set(membership.tenants.values_list("id", flat=True))


# --- Capabilities: cap name -> set of roles that hold it -------------------

CAP_ROLES = {
    "dashboard.view":   {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "log.view":         {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    # tenant.view is granted to every role so template/config forms can list the
    # user's own tenants; writes are far more restricted.
    "tenant.view":      {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN, DESIGN_ADMIN},
    "tenant.update":    {PLATFORM_ADMIN, TENANT_ADMIN},
    "tenant.create":    {PLATFORM_ADMIN},
    "tenant.delete":    {PLATFORM_ADMIN},
    "user.view":        {PLATFORM_ADMIN, TENANT_ADMIN},
    "user.manage":      {PLATFORM_ADMIN, TENANT_ADMIN},
    "template.view":    {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN, DESIGN_ADMIN},
    "template.manage":  {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN, DESIGN_ADMIN},
    "config.view":      {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "config.manage":    {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "integration.view": {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    # Enabling/disabling a provider is global, so it is platform-only.
    "integration.manage": {PLATFORM_ADMIN},
    "apikey.view":      {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "apikey.manage":    {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    # Every signed-in user may view and edit their own profile.
    "profile.view":     set(ALL_ROLES),
    "profile.manage":   set(ALL_ROLES),
    "meta.view":        set(ALL_ROLES),
}


def has_cap(role, cap):
    return role in CAP_ROLES.get(cap, set())


# --- Sidebar page access ---------------------------------------------------
# Keys match the PAGES list / URL names in views.py.

PAGE_ROLES = {
    "dashboard":      {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "logs":           {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "tenants":        {PLATFORM_ADMIN, TENANT_ADMIN},
    "users":          {PLATFORM_ADMIN, TENANT_ADMIN},
    "templates":      {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN, DESIGN_ADMIN},
    "configurations": {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "apikeys":        {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
    "integrations":   {PLATFORM_ADMIN, TENANT_ADMIN, CONFIG_ADMIN},
}

# Sidebar / landing order.
PAGE_ORDER = [
    "dashboard", "logs", "tenants", "users",
    "templates", "configurations", "apikeys", "integrations",
]


def can_access_page(role, key):
    return role in PAGE_ROLES.get(key, set())


def landing_page(role):
    """First page (in sidebar order) the role may access; falls back to logout."""
    for key in PAGE_ORDER:
        if can_access_page(role, key):
            return key
    return "logout"

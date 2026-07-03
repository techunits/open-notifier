import uuid
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import redirect, render
from django.template import Context
from django.template import Template as DjangoTemplate
from django.views.decorators.cache import never_cache

from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import Tenant, TenantApiKey
from templates.models import Template
from notifications.models import (
    Configuration,
    IntegrationState,
    NotificationLog,
    NOTIFICATION_TYPE_CHOICES,
    PROVIDER_STATUS_CHOICES,
    NOTIFICATION_STATUS_CHOICES,
)

from .integrations import discover_integrations, get_integration
from .models import Membership
from .roles import (
    ALL_ROLES,
    CAP_ROLES,
    CONFIG_ADMIN,
    DESIGN_ADMIN,
    PAGE_ORDER,
    PLATFORM_ADMIN,
    TENANT_ADMIN,
    TENANT_GRANTABLE_ROLES,
    accessible_tenant_ids,
    can_access_page,
    has_cap,
    landing_page,
    resolve_role,
)
from .serializers import (
    ConfigurationSerializer,
    NotificationLogSerializer,
    SelfProfileSerializer,
    TemplateSerializer,
    TenantApiKeySerializer,
    TenantSerializer,
    UserSerializer,
)


# ---------------------------------------------------------------------------
# Page (HTML) views
# ---------------------------------------------------------------------------

PAGES = [
    {"key": "dashboard", "label": "Dashboard", "icon": "grid"},
    {"key": "logs", "label": "Notification Logs", "icon": "activity"},
    {"key": "tenants", "label": "Tenants", "icon": "building"},
    {"key": "users", "label": "Users", "icon": "users"},
    {"key": "templates", "label": "Email Templates", "icon": "mail"},
    {"key": "configurations", "label": "Configurations", "icon": "sliders"},
    {"key": "apikeys", "label": "API Keys", "icon": "key"},
    {"key": "integrations", "label": "Integrations", "icon": "plug"},
]


@never_cache
def login_view(request):
    role = resolve_role(request.user)
    if role is not None:
        return redirect("en_console:" + landing_page(role))

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = "Invalid credentials. Please try again."
        elif resolve_role(user) is None:
            error = "This account does not have console access."
        else:
            auth_login(request, user)
            target = request.GET.get("next") or (
                "en_console:" + landing_page(resolve_role(user))
            )
            return redirect(target)

    return render(request, "en_console/login.html", {"error": error})


@never_cache
def logout_view(request):
    auth_logout(request)
    return redirect("en_console:login")


def _page(request, active, template):
    """Render a console page, gating it by the user's role and passing only the
    sidebar entries that role may access."""
    role = resolve_role(request.user)
    if role is None:
        return redirect("en_console:login")
    if not can_access_page(role, active):
        return redirect("en_console:" + landing_page(role))
    pages = [p for p in PAGES if can_access_page(role, p["key"])]
    return render(
        request,
        template,
        {"pages": pages, "active": active, "role": role},
    )


@login_required
def dashboard(request):
    return _page(request, "dashboard", "en_console/dashboard.html")


@login_required
def tenants_page(request):
    return _page(request, "tenants", "en_console/tenants.html")


@login_required
def users_page(request):
    return _page(request, "users", "en_console/users.html")


@login_required
def templates_page(request):
    return _page(request, "templates", "en_console/templates.html")


@login_required
def template_editor_page(request, pk=None):
    """Full-page template editor (new or edit) — gated by the templates page role."""
    role = resolve_role(request.user)
    if role is None:
        return redirect("en_console:login")
    if not can_access_page(role, "templates"):
        return redirect("en_console:" + landing_page(role))
    pages = [p for p in PAGES if can_access_page(role, p["key"])]
    return render(
        request,
        "en_console/template_editor.html",
        {
            "pages": pages,
            "active": "templates",
            "role": role,
            "template_id": str(pk) if pk else "",
        },
    )


@login_required
def configurations_page(request):
    return _page(request, "configurations", "en_console/configurations.html")


@login_required
def integrations_page(request):
    return _page(request, "integrations", "en_console/integrations.html")


@login_required
def logs_page(request):
    return _page(request, "logs", "en_console/logs.html")


@login_required
def apikeys_page(request):
    return _page(request, "apikeys", "en_console/apikeys.html")


@login_required
def profile_page(request):
    """Self-service profile page — reachable by any signed-in role (it is not a
    sidebar item, so it bypasses the per-page role gate)."""
    role = resolve_role(request.user)
    if role is None:
        return redirect("en_console:login")
    pages = [p for p in PAGES if can_access_page(role, p["key"])]
    return render(
        request,
        "en_console/profile.html",
        {"pages": pages, "active": None, "role": role},
    )


# ---------------------------------------------------------------------------
# API access control
# ---------------------------------------------------------------------------

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class RoleCapPermission(BasePermission):
    """Allow the request only if the user's role holds the capability the view
    requires for this HTTP method (``view.cap_for(method)``)."""

    message = "Your role does not permit this action."

    def has_permission(self, request, view):
        role = resolve_role(request.user)
        if role is None:
            return False
        cap = view.cap_for(request.method)
        return bool(cap) and has_cap(role, cap)


class AdminAPIMixin:
    """Session-authenticated, role-gated API access with CSRF enforcement.

    A view declares its required capabilities via ``read_cap`` (safe methods)
    and ``write_cap`` (unsafe methods), or overrides :meth:`cap_for` for
    method-specific rules.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, RoleCapPermission]
    read_cap = None
    write_cap = None

    def cap_for(self, method):
        return self.read_cap if method in SAFE_METHODS else self.write_cap

    @property
    def role(self):
        return resolve_role(self.request.user)


class TenantScopedMixin:
    """Restrict querysets and writes to the tenants the caller may access."""

    tenant_path = "tenant_id"

    def scope_queryset(self, qs):
        ids = accessible_tenant_ids(self.request.user)
        if ids is None:  # PLATFORM_ADMIN – unrestricted
            return qs
        return qs.filter(**{f"{self.tenant_path}__in": ids})

    def assert_tenant_allowed(self, tenant):
        ids = accessible_tenant_ids(self.request.user)
        if ids is None or tenant is None:
            return
        tid = getattr(tenant, "id", tenant)
        if tid not in ids:
            raise PermissionDenied("You do not have access to that tenant.")


class SoftDeleteMixin:
    """Mark ``is_deleted`` instead of physically removing the row."""

    def perform_destroy(self, instance):
        instance.is_deleted = True
        if hasattr(instance, "is_enabled"):
            instance.is_enabled = False
        instance.save()


# --- Choices / meta -------------------------------------------------------

class MetaView(AdminAPIMixin, APIView):
    """Static choices used to build forms on the client."""

    read_cap = "meta.view"

    def get(self, request):
        return Response(
            {
                "notification_types": [c[0] for c in NOTIFICATION_TYPE_CHOICES],
                "providers": [c[0] for c in PROVIDER_STATUS_CHOICES],
                "notification_statuses": [c[0] for c in NOTIFICATION_STATUS_CHOICES],
                "roles": [r[0] for r in Membership.ROLE_CHOICES],
                "api_key_expiry_options": [
                    {"value": d, "label": f"{d} days"} for d in TenantApiKey.EXPIRY_DAYS
                ] + [{"value": None, "label": "Never expire"}],
            }
        )


class MeView(AdminAPIMixin, APIView):
    """The signed-in user's role, tenant scope, and derived UI permissions."""

    read_cap = "meta.view"

    def get(self, request):
        role = resolve_role(request.user)
        ids = accessible_tenant_ids(request.user)
        if role == PLATFORM_ADMIN:
            grantable = list(ALL_ROLES)
        elif role == TENANT_ADMIN:
            grantable = [r for r in ALL_ROLES if r in TENANT_GRANTABLE_ROLES]
        else:
            grantable = []
        return Response(
            {
                "username": request.user.username,
                "role": role,
                "is_superuser": request.user.is_superuser,
                "all_tenants": ids is None,
                "tenant_ids": None if ids is None else [str(i) for i in ids],
                "pages": [k for k in PAGE_ORDER if can_access_page(role, k)],
                "caps": {c: has_cap(role, c) for c in CAP_ROLES},
                "grantable_roles": grantable,
            }
        )


class ProfileView(AdminAPIMixin, APIView):
    """The signed-in user's own profile (any role): view and self-edit."""

    def cap_for(self, method):
        return "profile.view" if method in SAFE_METHODS else "profile.manage"

    def get(self, request):
        return Response(SelfProfileSerializer(request.user).data)

    def _save(self, request):
        serializer = SelfProfileSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        return self._save(request)

    def patch(self, request):
        return self._save(request)


class ChangePasswordView(AdminAPIMixin, APIView):
    """Self-service password change: requires the current password and a
    confirmed new password. Available to any signed-in role."""

    read_cap = "profile.view"
    write_cap = "profile.manage"

    def post(self, request):
        user = request.user
        current = request.data.get("current_password") or ""
        new = request.data.get("new_password") or ""
        confirm = request.data.get("confirm_password") or ""

        if not current or not new or not confirm:
            raise ValidationError(
                {"detail": ["Current, new and confirm password are all required."]}
            )
        if not user.check_password(current):
            raise ValidationError({"current_password": ["Current password is incorrect."]})
        if new != confirm:
            raise ValidationError({"confirm_password": ["New passwords do not match."]})
        try:
            validate_password(new, user)
        except DjangoValidationError as exc:
            raise ValidationError({"new_password": list(exc.messages)})

        user.set_password(new)
        user.save()
        # Keep the current session alive after the password rotation.
        update_session_auth_hash(request, user)
        return Response({"message": "Password updated."})


class StatsView(AdminAPIMixin, APIView):
    """Aggregate counters for the dashboard, scoped to accessible tenants."""

    read_cap = "dashboard.view"

    def get(self, request):
        ids = accessible_tenant_ids(request.user)

        tenants = Tenant.objects.filter(is_deleted=False)
        templates = Template.objects.filter(is_deleted=False)
        configs = Configuration.objects.filter(is_deleted=False)
        logs = NotificationLog.objects.all()

        if ids is not None:
            tenants = tenants.filter(id__in=ids)
            templates = templates.filter(tenant_id__in=ids)
            configs = configs.filter(tenant_id__in=ids)
            logs = logs.filter(notification_ref__tenant_id__in=ids)
            users_count = (
                Membership.objects.filter(tenants__id__in=ids).distinct().count()
            )
        else:
            users_count = User.objects.count()

        return Response(
            {
                "tenants": tenants.count(),
                "users": users_count,
                "templates": templates.count(),
                "configurations": configs.count(),
                "integrations": len(discover_integrations()),
                "notifications": {
                    "total": logs.count(),
                    "success": logs.filter(status="SUCCESS").count(),
                    "failed": logs.filter(status="FAILED").count(),
                    "queued": logs.filter(status="QUEUED").count(),
                },
                "recent_logs": NotificationLogSerializer(
                    logs.order_by("-created_on")[:10], many=True
                ).data,
            }
        )


# --- Tenants --------------------------------------------------------------

class TenantListCreate(TenantScopedMixin, AdminAPIMixin, generics.ListCreateAPIView):
    serializer_class = TenantSerializer
    tenant_path = "id"

    def cap_for(self, method):
        return "tenant.view" if method in SAFE_METHODS else "tenant.create"

    def get_queryset(self):
        return self.scope_queryset(
            Tenant.objects.filter(is_deleted=False).order_by("name")
        )


class TenantDetail(TenantScopedMixin, AdminAPIMixin, SoftDeleteMixin,
                   generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TenantSerializer
    tenant_path = "id"

    def cap_for(self, method):
        if method in SAFE_METHODS:
            return "tenant.view"
        if method == "DELETE":
            return "tenant.delete"
        return "tenant.update"

    def get_queryset(self):
        return self.scope_queryset(Tenant.objects.filter(is_deleted=False))


# --- Users ----------------------------------------------------------------

class UserQuerysetMixin:
    """PLATFORM_ADMIN sees all users; TENANT_ADMIN only sees the CONFIG/DESIGN
    users associated with its own tenants."""

    def get_queryset(self):
        qs = User.objects.all().order_by("username")
        if self.role == PLATFORM_ADMIN:
            return qs
        ids = accessible_tenant_ids(self.request.user)
        return qs.filter(
            membership__role__in=list(TENANT_GRANTABLE_ROLES),
            membership__tenants__id__in=ids,
        ).distinct()


class UserListCreate(UserQuerysetMixin, AdminAPIMixin, generics.ListCreateAPIView):
    serializer_class = UserSerializer
    read_cap = "user.view"
    write_cap = "user.manage"


class UserDetail(UserQuerysetMixin, AdminAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    read_cap = "user.view"
    write_cap = "user.manage"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {"error": {"ref": "SELF_DELETE", "message": "You cannot delete your own account."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if instance.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            return Response(
                {"error": {"ref": "LAST_SUPERUSER", "message": "Cannot delete the last superuser."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Templates ------------------------------------------------------------

class TemplateMixin(TenantScopedMixin):
    """Shared tenant scoping + DESIGN_ADMIN 'EMAIL only' rule for templates."""

    def base_template_qs(self):
        qs = self.scope_queryset(Template.objects.filter(is_deleted=False))
        if self.role == DESIGN_ADMIN:
            # Design admins may only see/manage EMAIL-only templates.
            qs = qs.filter(notification_types=["EMAIL"])
        return qs

    def enforce_email_only(self, serializer):
        if self.role != DESIGN_ADMIN:
            return
        types = list(serializer.validated_data.get("notification_types") or [])
        if types != ["EMAIL"]:
            raise ValidationError(
                {"notification_types": ["Design admins can only manage EMAIL templates."]}
            )


class TemplateListCreate(TemplateMixin, AdminAPIMixin, generics.ListCreateAPIView):
    serializer_class = TemplateSerializer
    read_cap = "template.view"
    write_cap = "template.manage"

    def get_queryset(self):
        qs = self.base_template_qs().order_by("name")
        tenant = self.request.query_params.get("tenant")
        if tenant:
            qs = qs.filter(tenant_id=tenant)
        return qs

    def perform_create(self, serializer):
        self.assert_tenant_allowed(serializer.validated_data.get("tenant"))
        self.enforce_email_only(serializer)
        actor = uuid.uuid4()
        serializer.save(created_by=actor, modified_by=actor)


class TemplateDetail(TemplateMixin, AdminAPIMixin, SoftDeleteMixin,
                     generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TemplateSerializer
    read_cap = "template.view"
    write_cap = "template.manage"

    def get_queryset(self):
        return self.base_template_qs()

    def perform_update(self, serializer):
        self.assert_tenant_allowed(
            serializer.validated_data.get("tenant") or serializer.instance.tenant
        )
        self.enforce_email_only(serializer)
        serializer.save(modified_by=uuid.uuid4())


class TemplatePreviewView(AdminAPIMixin, APIView):
    """Render a template's subject/body with a sample payload (no DB write)."""

    def cap_for(self, method):
        return "template.view"

    def post(self, request):
        body = request.data.get("body", "") or ""
        subject = request.data.get("subject", "") or ""
        payload = request.data.get("payload", {}) or {}
        if not isinstance(payload, dict):
            payload = {}
        try:
            rendered_body = DjangoTemplate(body).render(Context(payload))
            rendered_subject = DjangoTemplate(subject).render(Context(payload))
        except Exception as exc:  # surface template syntax errors to the editor
            return Response(
                {"error": {"ref": "TEMPLATE_RENDER_ERROR", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"subject": rendered_subject, "body": rendered_body})


# --- Configurations -------------------------------------------------------

class ConfigurationListCreate(TenantScopedMixin, AdminAPIMixin,
                              generics.ListCreateAPIView):
    serializer_class = ConfigurationSerializer
    read_cap = "config.view"
    write_cap = "config.manage"

    def get_queryset(self):
        qs = self.scope_queryset(
            Configuration.objects.filter(is_deleted=False).order_by("notification_type")
        )
        # Configurations depend on their provider — hide any whose provider is
        # disabled on the Integrations page.
        qs = qs.filter(provider__in=IntegrationState.enabled_providers())
        tenant = self.request.query_params.get("tenant")
        if tenant:
            qs = qs.filter(tenant_id=tenant)
        return qs

    def perform_create(self, serializer):
        self.assert_tenant_allowed(serializer.validated_data.get("tenant"))
        serializer.save()


class ConfigurationDetail(TenantScopedMixin, AdminAPIMixin, SoftDeleteMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ConfigurationSerializer
    read_cap = "config.view"
    write_cap = "config.manage"

    def get_queryset(self):
        return self.scope_queryset(Configuration.objects.filter(is_deleted=False))

    def perform_update(self, serializer):
        self.assert_tenant_allowed(
            serializer.validated_data.get("tenant") or serializer.instance.tenant
        )
        serializer.save()


# --- Integrations ---------------------------------------------------------

class IntegrationList(AdminAPIMixin, APIView):
    read_cap = "integration.view"

    def get(self, request):
        ids = accessible_tenant_ids(request.user)
        enabled = IntegrationState.enabled_providers()
        integrations = discover_integrations()
        for manifest in integrations:
            configs = Configuration.objects.filter(
                provider=manifest.get("provider"), is_deleted=False
            )
            if ids is not None:
                configs = configs.filter(tenant_id__in=ids)
            manifest["configuration_count"] = configs.count()
            manifest["is_enabled"] = manifest.get("provider") in enabled
        return Response({"integrations": integrations})


class IntegrationDetail(AdminAPIMixin, APIView):
    read_cap = "integration.view"
    write_cap = "integration.manage"

    def get(self, request, key):
        manifest = get_integration(key)
        if manifest is None:
            return Response(
                {"error": {"ref": "INTEGRATION_NOT_FOUND", "message": "Unknown integration."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        ids = accessible_tenant_ids(request.user)
        configs = Configuration.objects.filter(
            provider=manifest.get("provider"), is_deleted=False
        )
        if ids is not None:
            configs = configs.filter(tenant_id__in=ids)
        manifest["configurations"] = ConfigurationSerializer(configs, many=True).data
        manifest["is_enabled"] = IntegrationState.is_provider_enabled(manifest.get("provider"))
        return Response(manifest)

    def patch(self, request, key):
        """Enable/disable the provider globally (platform admins only)."""
        manifest = get_integration(key)
        if manifest is None:
            return Response(
                {"error": {"ref": "INTEGRATION_NOT_FOUND", "message": "Unknown integration."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        provider = manifest.get("provider")
        is_enabled = bool(request.data.get("is_enabled"))
        IntegrationState.objects.update_or_create(
            provider=provider, defaults={"is_enabled": is_enabled}
        )
        return Response({"provider": provider, "is_enabled": is_enabled})


# --- Tenant API keys ------------------------------------------------------

class TenantApiKeyListCreate(TenantScopedMixin, AdminAPIMixin, generics.ListCreateAPIView):
    """List a tenant's API keys, or mint a new one.

    Creation returns the raw key **once** (as ``api_key``); afterwards only the
    SHA3-512 hash is stored and just the last 6 characters are shown.
    """

    serializer_class = TenantApiKeySerializer
    read_cap = "apikey.view"
    write_cap = "apikey.manage"
    tenant_path = "tenant_id"

    def get_queryset(self):
        qs = self.scope_queryset(
            TenantApiKey.objects.filter(is_deleted=False)
            .select_related("tenant")
            .order_by("-created_on")
        )
        tenant = self.request.query_params.get("tenant")
        if tenant:
            qs = qs.filter(tenant_id=tenant)
        return qs

    def create(self, request, *args, **kwargs):
        tenant_id = request.data.get("tenant")
        tenant = Tenant.objects.filter(id=tenant_id, is_deleted=False).first() if tenant_id else None
        if tenant is None:
            raise ValidationError({"tenant": ["A valid tenant is required."]})
        self.assert_tenant_allowed(tenant)

        label = (request.data.get("label") or "").strip()
        if not label:
            raise ValidationError({"label": ["A label is required."]})

        # Validate expiry against the allowed windows (None == never expire).
        raw_days = request.data.get("expires_in_days", None)
        expires_on = None
        if raw_days is not None:
            try:
                days = int(raw_days)
            except (TypeError, ValueError):
                raise ValidationError({"expires_in_days": ["Invalid expiry."]})
            if days not in TenantApiKey.EXPIRY_DAYS:
                raise ValidationError(
                    {"expires_in_days": [f"Choose one of {TenantApiKey.EXPIRY_DAYS} days, or never."]}
                )
            expires_on = timezone.now() + timedelta(days=days)

        raw_key = TenantApiKey.generate_raw_key()
        api_key = TenantApiKey.objects.create(
            tenant=tenant,
            label=label,
            key_hash=TenantApiKey.hash_key(raw_key),
            last_six=raw_key[-6:],
            expires_on=expires_on,
        )
        data = TenantApiKeySerializer(api_key).data
        data["api_key"] = raw_key  # shown exactly once
        return Response(data, status=status.HTTP_201_CREATED)


class TenantApiKeyDetail(TenantScopedMixin, AdminAPIMixin,
                         generics.RetrieveUpdateDestroyAPIView):
    """Edit an API key's label (PATCH) or revoke it (DELETE)."""

    serializer_class = TenantApiKeySerializer
    read_cap = "apikey.view"
    write_cap = "apikey.manage"
    tenant_path = "tenant_id"

    def get_queryset(self):
        return self.scope_queryset(TenantApiKey.objects.filter(is_deleted=False))

    def perform_destroy(self, instance):
        # Revoke: deactivate and hide, but keep the row for auditing.
        instance.is_active = False
        instance.is_deleted = True
        instance.save()


# --- Notification logs ----------------------------------------------------

class NotificationLogList(TenantScopedMixin, AdminAPIMixin, generics.ListAPIView):
    """Delivery log for every notification, newest first.

    Supports ``?status=`` (one of NOTIFICATION_STATUS_CHOICES) and ``?tenant=``
    filters, scoped to the caller's tenants. Capped at the 500 most recent rows.
    """

    serializer_class = NotificationLogSerializer
    read_cap = "log.view"
    tenant_path = "notification_ref__tenant_id"
    MAX_ROWS = 500

    def get_queryset(self):
        qs = self.scope_queryset(
            NotificationLog.objects.select_related(
                "notification_ref", "notification_ref__tenant"
            ).order_by("-created_on")
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        tenant = self.request.query_params.get("tenant")
        if tenant:
            qs = qs.filter(notification_ref__tenant_id=tenant)

        return qs[: self.MAX_ROWS]

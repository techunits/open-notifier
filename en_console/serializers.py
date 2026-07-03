from django.contrib.auth.models import User
from rest_framework import serializers

from tenants.models import Tenant, TenantApiKey
from templates.models import Template
from notifications.models import Configuration, NotificationLog

from .integrations import get_integration_by_provider
from .metadata import validate_metadata
from .models import Membership
from .roles import (
    PLATFORM_ADMIN,
    TENANT_ADMIN,
    TENANT_GRANTABLE_ROLES,
    accessible_tenant_ids,
    resolve_role,
)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "is_enabled",
            "is_deleted",
            "created_on",
            "modified_on",
        ]
        read_only_fields = ["id", "is_deleted", "created_on", "modified_on"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )
    # Console role + associated tenants live on the related Membership; they are
    # accepted on write and added to the representation from that Membership.
    role = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    tenants = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            "password",
            "role",
            "tenants",
        ]
        read_only_fields = ["id", "last_login", "date_joined"]

    # -- representation -----------------------------------------------------

    @staticmethod
    def _membership(instance):
        try:
            return instance.membership
        except Membership.DoesNotExist:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        membership = self._membership(instance)
        if membership is not None:
            tenant_ids = list(membership.tenants.values_list("id", flat=True))
            data["role"] = membership.role
            data["tenants"] = [str(t) for t in tenant_ids]
            data["tenant_names"] = list(
                membership.tenants.values_list("name", flat=True)
            )
        elif instance.is_superuser:
            data["role"] = PLATFORM_ADMIN
            data["tenants"] = []
            data["tenant_names"] = []
        else:
            data["role"] = None
            data["tenants"] = []
            data["tenant_names"] = []
        return data

    # -- validation ---------------------------------------------------------

    def validate(self, attrs):
        request = self.context.get("request")
        requester_role = resolve_role(request.user) if request else None

        role = attrs.get("role")
        role = role or None  # normalise "" -> None
        is_super = attrs.get(
            "is_superuser",
            getattr(self.instance, "is_superuser", False),
        )

        if requester_role == TENANT_ADMIN:
            # A tenant admin may only grant scoped, non-platform roles.
            if is_super:
                raise serializers.ValidationError(
                    {"is_superuser": ["You cannot grant superuser access."]}
                )
            if role not in TENANT_GRANTABLE_ROLES:
                raise serializers.ValidationError(
                    {"role": ["You can only assign CONFIG_ADMIN or DESIGN_ADMIN."]}
                )
            allowed = accessible_tenant_ids(request.user) or set()
            requested = {str(t) for t in (attrs.get("tenants") or [])}
            if not requested:
                raise serializers.ValidationError(
                    {"tenants": ["Select at least one tenant."]}
                )
            if not requested.issubset({str(t) for t in allowed}):
                raise serializers.ValidationError(
                    {"tenants": ["One or more tenants are outside your scope."]}
                )
            # Force safe flags for tenant-managed accounts.
            attrs["is_superuser"] = False
            attrs["is_staff"] = True
        else:  # PLATFORM_ADMIN (or unrestricted system caller)
            if self.instance is None and role is None:
                raise serializers.ValidationError(
                    {"role": ["A role is required."]}
                )
            # Staff/superuser are derived from the role, never set by hand:
            # every console user is staff, and PLATFORM_ADMIN implies a Django
            # superuser. (Only applied when a role is supplied, so a partial
            # update that leaves the role untouched keeps the existing flags.)
            if role is not None:
                attrs["is_staff"] = True
                attrs["is_superuser"] = role == PLATFORM_ADMIN

        return attrs

    # -- persistence --------------------------------------------------------

    def _apply_membership(self, user, role, tenant_ids):
        role = role or None
        if role is None:
            # No explicit role: drop any membership (a superuser is implicitly
            # PLATFORM_ADMIN via role resolution).
            Membership.objects.filter(user=user).delete()
            return
        membership, _ = Membership.objects.get_or_create(
            user=user, defaults={"role": role}
        )
        membership.role = role
        membership.save()
        if role == PLATFORM_ADMIN:
            membership.tenants.clear()
        elif tenant_ids is not None:
            membership.tenants.set(
                Tenant.objects.filter(id__in=tenant_ids, is_deleted=False)
            )

    def create(self, validated_data):
        role = validated_data.pop("role", None)
        tenant_ids = validated_data.pop("tenants", None)
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        self._apply_membership(user, role, tenant_ids)
        return user

    def update(self, instance, validated_data):
        role_given = "role" in validated_data
        tenants_given = "tenants" in validated_data
        role = validated_data.pop("role", None)
        tenant_ids = validated_data.pop("tenants", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if role_given:
            self._apply_membership(
                instance, role, tenant_ids if tenants_given else None
            )
        elif tenants_given:
            membership = self._membership(instance)
            if membership is not None and membership.role != PLATFORM_ADMIN:
                membership.tenants.set(
                    Tenant.objects.filter(id__in=tenant_ids or [], is_deleted=False)
                )
        return instance


class SelfProfileSerializer(serializers.ModelSerializer):
    """The signed-in user editing their *own* account details: name, email and
    username. Password changes go through a dedicated endpoint; role, tenants
    and staff/superuser flags are read-only here (admin-governed)."""

    role = serializers.SerializerMethodField()
    tenant_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "tenant_names",
            "is_superuser",
        ]
        read_only_fields = ["role", "tenant_names", "is_superuser"]

    def get_role(self, obj):
        return resolve_role(obj)

    def get_tenant_names(self, obj):
        try:
            return list(obj.membership.tenants.values_list("name", flat=True))
        except Membership.DoesNotExist:
            return []

    def validate_username(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Username is required.")
        qs = User.objects.filter(username=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("That username is already taken.")
        return value


class TemplateSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = Template
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "name",
            "ref",
            "notification_types",
            "subject",
            "body",
            "addon_data",
            "is_enabled",
            "is_deleted",
            "created_on",
            "modified_on",
        ]
        read_only_fields = [
            "id",
            "tenant_name",
            "is_deleted",
            "created_on",
            "modified_on",
        ]


class ConfigurationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = Configuration
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "notification_type",
            "provider",
            "metadata",
            "is_default",
            "is_enabled",
            "is_deleted",
            "created_on",
            "modified_on",
        ]
        read_only_fields = [
            "id",
            "tenant_name",
            "is_deleted",
            "created_on",
            "modified_on",
        ]

    def validate_provider(self, value):
        # PROVIDER_STATUS_CHOICES is discovered from the filesystem at startup;
        # the model no longer enforces choices, so validate here.
        from notifications.models import PROVIDER_STATUS_CHOICES

        valid = {c[0] for c in PROVIDER_STATUS_CHOICES}
        if value not in valid:
            raise serializers.ValidationError("Unknown provider.")
        return value

    def validate(self, attrs):
        """Validate ``metadata`` against the selected provider's manifest.

        Mirrors the client-side rules on the Configurations page. The metadata
        is still persisted verbatim as raw JSON (with number/boolean fields
        coerced to their proper JSON types).
        """
        provider = attrs.get("provider") or getattr(self.instance, "provider", None)
        if "metadata" in attrs:
            metadata = attrs["metadata"]
        elif self.instance is not None:
            metadata = self.instance.metadata
        else:
            metadata = {}

        manifest = get_integration_by_provider(provider)
        config_fields = manifest.get("config_fields") if manifest else None
        cleaned, errors = validate_metadata(config_fields, metadata)
        if errors:
            raise serializers.ValidationError({"metadata": errors})
        attrs["metadata"] = cleaned
        return attrs


class NotificationLogSerializer(serializers.ModelSerializer):
    # Display helpers pulled from the related Configuration / stored metadata so
    # the logs list can show human-readable context without extra requests.
    tenant_name = serializers.CharField(
        source="notification_ref.tenant.name", read_only=True
    )
    provider = serializers.CharField(
        source="notification_ref.provider", read_only=True
    )
    notification_type = serializers.CharField(
        source="notification_ref.notification_type", read_only=True
    )
    template_ref = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "notification_ref",
            "tenant_name",
            "provider",
            "notification_type",
            "template_ref",
            "status",
            "metadata",
            "created_on",
            "modified_on",
        ]
        read_only_fields = fields

    def get_template_ref(self, obj):
        return (obj.metadata or {}).get("template_ref")


class TenantApiKeySerializer(serializers.ModelSerializer):
    """Read + label-edit view of a tenant API key. Never exposes the key hash;
    the raw key is only returned once, by the create view."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = TenantApiKey
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "label",
            "last_six",
            "expires_on",
            "is_active",
            "is_expired",
            "last_used_on",
            "created_on",
        ]
        # Only the label is editable (via PATCH); everything else is set at
        # creation or derived.
        read_only_fields = [
            "id",
            "tenant",
            "tenant_name",
            "last_six",
            "expires_on",
            "is_active",
            "is_expired",
            "last_used_on",
            "created_on",
        ]

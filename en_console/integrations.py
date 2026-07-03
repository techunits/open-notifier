"""Discovery utilities for notification integrations.

Integrations live under ``notifications/integrations/<key>/`` and each package
ships a ``sender.py`` (the worker that delivers the message) and an optional
``MANIFEST`` dict in its ``__init__.py`` describing the provider and the
configuration fields it expects. The admin panel uses this module to list the
available providers and to render provider-specific configuration forms.
"""
import importlib
import os

from django.conf import settings

INTEGRATIONS_DIR = os.path.join(settings.BASE_DIR, "notifications", "integrations")


def _default_manifest(key):
    """Fallback manifest for an integration that ships no MANIFEST dict."""
    return {
        "key": key,
        "provider": key.upper(),
        "name": key.replace("_", " ").title(),
        "notification_type": "EMAIL",
        "description": "",
        "config_fields": [],
    }


def discover_integrations():
    """Return a list of manifest dicts for every installed integration.

    An integration is any sub-package of ``notifications/integrations`` that
    contains a ``sender.py`` module. The list is sorted by display name.
    """
    integrations = []
    if not os.path.isdir(INTEGRATIONS_DIR):
        return integrations

    for entry in sorted(os.listdir(INTEGRATIONS_DIR)):
        package_dir = os.path.join(INTEGRATIONS_DIR, entry)
        if entry.startswith("_") or not os.path.isdir(package_dir):
            continue
        if not os.path.exists(os.path.join(package_dir, "sender.py")):
            continue

        manifest = _default_manifest(entry)
        try:
            # Only the lightweight package __init__ (MANIFEST/LOGO) is imported
            # here — never the sender module — so a broken delivery dependency
            # (requests, boto3, SMTP, …) can't blank out a provider's fields.
            module = importlib.import_module(f"notifications.integrations.{entry}")
            manifest.update(getattr(module, "MANIFEST", {}) or {})
        except Exception as exc:  # defensive: never break the panel, but be loud
            logger = getattr(settings, "LOGGER", None)
            if logger:
                logger.error(f"Failed to load integration manifest '{entry}': {exc}")
        manifest["key"] = entry
        manifest.setdefault("has_sender", True)
        integrations.append(manifest)

    integrations.sort(key=lambda m: m.get("name", m["key"]).lower())
    return integrations


def get_integration(key):
    """Return the manifest for a single integration ``key`` or ``None``."""
    for manifest in discover_integrations():
        if manifest["key"] == key:
            return manifest
    return None


def get_integration_by_provider(provider):
    """Return the manifest matching a ``Configuration.provider`` value."""
    for manifest in discover_integrations():
        if manifest.get("provider") == provider:
            return manifest
    return None

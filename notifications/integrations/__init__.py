"""Notification delivery integrations.

Each sub-package ships:
  * a lightweight ``MANIFEST`` (+ ``LOGO``) in its ``__init__`` — read by the
    admin panel to discover providers and render their configuration form, and
  * a ``sender.py`` Celery worker that actually delivers the notification.

The manifest is intentionally kept free of heavy imports (celery, requests,
boto3, SMTP, …). Importing a provider package to read its manifest must never
pull in the delivery dependencies — otherwise a single missing/broken runtime
dependency would blank out *every* provider's config fields in the UI. The
sender modules are therefore imported lazily, via :func:`autoload_senders`
(called from ``notifications.tasks``) for Celery registration, and via
``importlib`` at send time.
"""
import importlib
import os

_DIR = os.path.dirname(__file__)


def iter_integration_keys():
    """Yield the directory name of every integration that has a ``sender.py``."""
    for entry in sorted(os.listdir(_DIR)):
        if entry.startswith("_") or not os.path.isdir(os.path.join(_DIR, entry)):
            continue
        if os.path.exists(os.path.join(_DIR, entry, "sender.py")):
            yield entry


def discover_provider_choices():
    """Scan the integration packages and return provider ``(value, label)`` choices.

    Called once at model-import time so ``PROVIDER_STATUS_CHOICES`` is populated
    from the filesystem instead of being hardcoded — dropping in a new provider
    package registers it automatically (after a restart). The provider value is
    ``MANIFEST['provider']`` when present, otherwise the uppercased directory
    name (the lowercased provider must equal the directory name — the dispatch
    convention in ``notifications/tasks.py``).
    """
    import importlib

    choices, seen = [], set()
    for entry in iter_integration_keys():
        provider = entry.upper()
        try:
            module = importlib.import_module(f"notifications.integrations.{entry}")
            provider = (getattr(module, "MANIFEST", {}) or {}).get("provider", provider)
        except Exception:  # never let a broken package break model import
            pass
        if provider not in seen:
            seen.add(provider)
            choices.append((provider, provider))
    return choices


def autoload_senders():
    """Import every integration ``sender`` module so their Celery tasks register.

    Called from ``notifications.tasks`` (which Celery autodiscovers). A failure
    for one provider is logged but never aborts loading the others.
    """
    from django.conf import settings

    logger = getattr(settings, "LOGGER", None)
    for entry in iter_integration_keys():
        try:
            importlib.import_module(f"notifications.integrations.{entry}.sender")
        except Exception as exc:  # pragma: no cover - defensive
            if logger:
                logger.error(f"Failed to load integration sender '{entry}': {exc}")

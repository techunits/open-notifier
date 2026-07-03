from celery import shared_task
from notifications.models import NotificationLog, IntegrationState
from django.conf import settings
import os
import importlib
from notifications.integrations import autoload_senders

logger = settings.LOGGER

# Register every integration's sender task with Celery. This is the worker-side
# entry point (notifications.tasks is autodiscovered), and it is resilient: a
# provider whose sender fails to import is logged and skipped, never breaking
# the others or the rest of the app.
autoload_senders()


@shared_task
def send_notification(notification_id):
    # pull up notification details
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception as e:
        logger.error(f"Invalid notification id: {notification_id}")
        return

    # Global kill-switch: suppress all EMAIL delivery when configured.
    if getattr(settings, "DISABLE_EMAIL_SENDING", False) and (
        notification_obj.notification_ref.notification_type == "EMAIL"
    ):
        logger.warning(
            f"Email sending is disabled; skipping notification {notification_id}"
        )
        notification_obj.status = "FAILED"
        metadata = notification_obj.metadata or {}
        metadata["response"] = {
            "message": "Email sending is disabled (DISABLE_EMAIL_SENDING is on)."
        }
        notification_obj.metadata = metadata
        notification_obj.save()
        return

    # Provider must be enabled on the console Integrations page (new providers
    # are disabled by default).
    provider = notification_obj.notification_ref.provider
    if not IntegrationState.is_provider_enabled(provider):
        logger.warning(
            f"Provider {provider} is disabled; skipping notification {notification_id}"
        )
        notification_obj.status = "FAILED"
        metadata = notification_obj.metadata or {}
        metadata["response"] = {"message": f"Provider {provider} is disabled."}
        notification_obj.metadata = metadata
        notification_obj.save()
        return

    integration_path = os.path.join(
        settings.BASE_DIR,
        "notifications",
        "integrations",
        notification_obj.notification_ref.provider.lower(),
        f"sender.py",
    )
    if os.path.exists(integration_path):
        logger.info(
            f"{notification_obj.notification_ref.notification_type} integration found({notification_id}): {notification_obj.notification_ref.provider}"
        )
        module_name = f"notifications.integrations.{notification_obj.notification_ref.provider.lower()}.sender"
        logger.info(f"Importing module: {module_name}")
        integration_module = importlib.import_module(module_name)
        integration_func = getattr(integration_module, "send")
        logger.info(
            f"Scheduling {notification_obj.notification_ref.notification_type} task({notification_id}): {notification_obj.notification_ref}"
        )
        integration_func.delay(notification_id)
    else:
        logger.error(
            f"{notification_obj.notification_ref.notification_type} integration not found({notification_id}): {notification_obj.notification_ref.provider}"
        )

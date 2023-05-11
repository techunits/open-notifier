from celery import shared_task
from notifications.models import NotificationLog
from django.conf import settings
import os
import importlib
from notifications.integrations import *

logger = settings.LOGGER


@shared_task
def send_notification(notification_id):
    # pull up notification details
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception as e:
        logger.error(f"Invalid notification id: {notification_id}")

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

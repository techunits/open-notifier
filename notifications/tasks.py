from celery import shared_task
from notifications.models import NotificationLog
from notifications.integrations.email.local_email import send as send_email_notification
from django.conf import settings
import os
import importlib

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
        notification_obj.notification_ref.notification_type.lower(),
        f"{notification_obj.notification_ref.provider.lower()}.py",
    )
    if os.path.exists(integration_path):
        logger.info(
            f"{notification_obj.notification_ref.notification_type} integration found({notification_id}): {notification_obj.notification_ref.provider}"
        )
        # module_name = f"email.{notification_obj.notification_ref.provider.lower()}.send"
        # logger.debug(f"Importing module: {module_name}")
        # integration_module = importlib.import_module(module_name, package='.')
        logger.info(
            f"Scheduling {notification_obj.notification_ref.notification_type} task({notification_id}): {notification_obj.notification_ref}"
        )
        send_email_notification.delay(notification_id)
    else:
        logger.error(
            f"{notification_obj.notification_ref.notification_type} integration found({notification_id}): {notification_obj.notification_ref.provider}"
        )

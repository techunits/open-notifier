import traceback
from celery import shared_task

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from notifications.models import NotificationLog

from django.conf import settings

logger = settings.LOGGER


# The local MTA (Postfix) is always reached directly on the loopback interface
# with no authentication or TLS — these are fixed, not configurable.
LOCAL_MTA_HOST = "127.0.0.1"
LOCAL_MTA_PORT = 25


@shared_task
def send(notification_id):
    """Deliver an email straight through the local Postfix / MTA.

    A local Postfix relay listens on 127.0.0.1:25 and accepts mail without
    authentication, so there are no SMTP settings to configure — only the
    sender address (``from_email``) comes from the configuration.
    """
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception:
        logger.error(f"Invalid notification id: {notification_id}")
        return

    notification_obj.status = "PROCESSING"
    notification_obj.save()
    config_obj = notification_obj.notification_ref
    md = config_obj.metadata or {}

    # Connect directly to the local MTA — no host/port/user/pass/TLS options.
    email_backend = EmailBackend(
        host=LOCAL_MTA_HOST,
        port=LOCAL_MTA_PORT,
        username=None,
        password=None,
        use_tls=False,
        fail_silently=False,
    )

    subject = notification_obj.metadata.get("subject")
    body = notification_obj.metadata.get("body")
    # `smtp_from_email` kept as a fallback for legacy LOCAL_EMAIL configs.
    from_email = (
        notification_obj.metadata.get("from")
        or md.get("from_email")
        or md.get("smtp_from_email")
        or "root@localhost"
    )

    logger.info(f"Sending local email to: {notification_obj.metadata.get('to', [])}")
    try:
        email_msg_obj = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=notification_obj.metadata.get("to", []),
            cc=notification_obj.metadata.get("cc", []),
            bcc=notification_obj.metadata.get("bcc", []),
            connection=email_backend,
        )
        email_msg_obj.content_subtype = "html"
        email_msg_obj.send()
        response = {"message": "SUCCESS"}
        status = "SUCCESS"
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        response = {"error": str(e)}
        status = "FAILED"

    notification_obj.status = status
    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    notification_obj.save()

import traceback
from celery import shared_task

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from notifications.models import NotificationLog, Configuration

from django.conf import settings

logger = settings.LOGGER


@shared_task
def send(notification_id):
    # pull up notification details
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception as e:
        logger.error(f"Invalid notification id: {notification_id}")

    notification_obj.status = "PROCESSING"
    notification_obj.save()
    config_obj = notification_obj.notification_ref

    # initialize the SMTP connection params
    email_backend = EmailBackend(
        host=config_obj.metadata.get("smtp_host"),
        port=config_obj.metadata.get("smtp_port"),
        username=config_obj.metadata.get("smtp_username"),
        password=config_obj.metadata.get("smtp_password"),
        use_tls=True,
        fail_silently=False,
    )

    subject = notification_obj.metadata.get("subject")
    body = notification_obj.metadata.get("body")

    from_email = notification_obj.metadata.get("from")
    if not from_email:
        from_email = config_obj.metadata.get("smtp_from_email", "test@example.com")

    logger.info(f"Sending email to: {notification_obj.metadata.get('to', [])}")
    logger.info(f"Sending email from: {from_email}")
    logger.info(f"Subject: {subject}")
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
        response = {
            "message": "SUCCESS",
        }
        status = "SUCCESS"
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        response = {
            "error": str(e)
        }
        status = "FAILED"

    notification_obj.status = status
    notification_obj.metadata.update({
        "response": response
    })
    logger.info(f"{config_obj} Status({notification_id}): " + notification_obj.status)
    notification_obj.save()

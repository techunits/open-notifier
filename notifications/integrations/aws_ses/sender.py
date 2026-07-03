import traceback
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "aws_region": "us-east-1",
  "aws_access_key_id": "AKIAxxxxxxxxxxxxxxxx",
  "aws_secret_access_key": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "from_email": "no-reply@example.com"
}

Requires the `boto3` package (see requirements.txt).
"""


@shared_task
def send(notification_id):
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception:
        logger.error(f"Invalid notification id: {notification_id}")
        return

    notification_obj.status = "PROCESSING"
    notification_obj.save()
    config_obj = notification_obj.notification_ref
    md = config_obj.metadata or {}

    subject = notification_obj.metadata.get("subject")
    body = notification_obj.metadata.get("body")
    to = notification_obj.metadata.get("to", [])
    cc = notification_obj.metadata.get("cc", [])
    bcc = notification_obj.metadata.get("bcc", [])
    from_email = notification_obj.metadata.get("from") or md.get("from_email")

    try:
        import boto3  # lazy import so the dependency is only needed for AWS SES

        client = boto3.client(
            "ses",
            region_name=md.get("aws_region"),
            aws_access_key_id=md.get("aws_access_key_id"),
            aws_secret_access_key=md.get("aws_secret_access_key"),
        )
        resp = client.send_email(
            Source=from_email,
            Destination={"ToAddresses": to, "CcAddresses": cc, "BccAddresses": bcc},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        status = "SUCCESS"
        response = {"message": "SUCCESS", "message_id": resp.get("MessageId")}
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        status = "FAILED"
        response = {"error": str(e)}

    notification_obj.status = status
    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    notification_obj.save()

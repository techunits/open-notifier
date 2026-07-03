import traceback
import requests
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "api_base_url": "https://mandrillapp.com/api/1.0",
  "api_key": "xxxxxxxxxxxxxxxxxxxxxx",
  "from_email": "no-reply@example.com",
  "from_name": "Example"
}

Uses the Mailchimp Transactional (Mandrill) messages/send API.
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

    base_url = md.get("api_base_url", "https://mandrillapp.com/api/1.0").rstrip("/")
    endpoint = f"{base_url}/messages/send.json"

    recipients = [{"email": e, "type": "to"} for e in to]
    recipients += [{"email": e, "type": "cc"} for e in cc]
    recipients += [{"email": e, "type": "bcc"} for e in bcc]

    payload = {
        "key": md.get("api_key"),
        "message": {
            "html": body,
            "subject": subject,
            "from_email": from_email,
            "from_name": md.get("from_name", ""),
            "to": recipients,
        },
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=30)
        result = resp.json() if resp.content else {}
        # A successful Mandrill call returns a list of per-recipient statuses.
        if resp.status_code == 200 and isinstance(result, list):
            rejected = [r for r in result if r.get("status") in ("rejected", "invalid")]
            status = "FAILED" if rejected else "SUCCESS"
            response = {"message": status, "data": result}
        else:
            status = "FAILED"
            response = {"error": result, "status_code": resp.status_code}
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        status = "FAILED"
        response = {"error": str(e)}

    notification_obj.status = status
    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    notification_obj.save()

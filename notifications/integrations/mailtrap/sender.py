import traceback
import requests
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "api_base_url": "https://send.api.mailtrap.io",
  "api_token": "xxxxxxxxxxxxxxxxxxxxxx",
  "from_email": "no-reply@example.com",
  "from_name": "Example"
}
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

    base_url = md.get("api_base_url", "https://send.api.mailtrap.io").rstrip("/")
    endpoint = f"{base_url}/api/send"
    headers = {
        "Authorization": f"Bearer {md.get('api_token')}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": {"email": from_email, "name": md.get("from_name", "")},
        "to": [{"email": e} for e in to],
        "subject": subject,
        "html": body,
    }
    if cc:
        payload["cc"] = [{"email": e} for e in cc]
    if bcc:
        payload["bcc"] = [{"email": e} for e in bcc]

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        result = resp.json() if resp.content else {}
        if resp.status_code in (200, 201, 202) and result.get("success"):
            status = "SUCCESS"
            response = {"message": "SUCCESS", "message_ids": result.get("message_ids")}
        else:
            status = "FAILED"
            response = {"error": result or resp.text, "status_code": resp.status_code}
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        status = "FAILED"
        response = {"error": str(e)}

    notification_obj.status = status
    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    notification_obj.save()

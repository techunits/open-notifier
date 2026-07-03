import traceback
import requests
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "api_base_url": "https://api.elasticemail.com/v2",
  "api_key": "00000000-0000-0000-0000-000000000000",
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
    from_email = notification_obj.metadata.get("from") or md.get("from_email")

    base_url = md.get("api_base_url", "https://api.elasticemail.com/v2").rstrip("/")
    endpoint = f"{base_url}/email/send"
    data = {
        "apikey": md.get("api_key"),
        "from": from_email,
        "fromName": md.get("from_name", ""),
        "to": ",".join(to),
        "subject": subject,
        "bodyHtml": body,
        "isTransactional": True,
    }

    try:
        resp = requests.post(endpoint, data=data, timeout=30)
        payload = resp.json() if resp.content else {}
        if resp.status_code == 200 and payload.get("success"):
            status = "SUCCESS"
            response = {"message": "SUCCESS", "data": payload.get("data")}
        else:
            status = "FAILED"
            response = {"error": payload.get("error", resp.text), "status_code": resp.status_code}
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        status = "FAILED"
        response = {"error": str(e)}

    notification_obj.status = status
    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    notification_obj.save()

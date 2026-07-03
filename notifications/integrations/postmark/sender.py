import traceback
import requests
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "api_base_url": "https://api.postmarkapp.com",
  "server_token": "00000000-0000-0000-0000-000000000000",
  "from_email": "no-reply@example.com",
  "from_name": "Example",
  "message_stream": "outbound"
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
    from_name = md.get("from_name", "")

    base_url = md.get("api_base_url", "https://api.postmarkapp.com").rstrip("/")
    endpoint = f"{base_url}/email"
    headers = {
        "X-Postmark-Server-Token": md.get("server_token"),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "From": f"{from_name} <{from_email}>" if from_name else from_email,
        "To": ",".join(to),
        "Subject": subject,
        "HtmlBody": body,
        "MessageStream": md.get("message_stream", "outbound"),
    }
    if cc:
        payload["Cc"] = ",".join(cc)
    if bcc:
        payload["Bcc"] = ",".join(bcc)

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        result = resp.json() if resp.content else {}
        if resp.status_code == 200 and result.get("ErrorCode") == 0:
            status = "SUCCESS"
            response = {"message": "SUCCESS", "message_id": result.get("MessageID")}
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

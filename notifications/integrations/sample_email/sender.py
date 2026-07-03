# =============================================================================
# BOILERPLATE sender — the Celery worker that actually delivers a message.
#
# Contract:
#   * Expose a Celery task named `send` that takes a NotificationLog id.
#   * Move the log through PROCESSING -> SUCCESS / FAILED and store the provider
#     response under metadata["response"].
#   * Read delivery credentials from `config_obj.metadata` (the Configuration's
#     saved fields) and the message from `notification_obj.metadata`.
#   * Put heavy imports (requests, boto3, SMTP, …) at module top — this module is
#     imported lazily (only when actually sending), never to read the manifest.
# =============================================================================
import traceback
import requests
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG (what an admin saves on the Configuration form)
{
  "api_base_url": "https://api.example.com/v1",
  "api_key": "xxxxxxxxxxxxxxxxxxxxxx",
  "from_email": "no-reply@example.com",
  "from_name": "Example"
}
"""


@shared_task
def send(notification_id):
    # 1) Load the notification log row.
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception:
        logger.error(f"Invalid notification id: {notification_id}")
        return

    notification_obj.status = "PROCESSING"
    notification_obj.save()

    config_obj = notification_obj.notification_ref      # the Configuration
    md = config_obj.metadata or {}                       # saved provider settings

    # 2) Pull the rendered message + recipients from the notification metadata.
    subject = notification_obj.metadata.get("subject")
    body = notification_obj.metadata.get("body")          # rendered HTML
    to = notification_obj.metadata.get("to", [])
    cc = notification_obj.metadata.get("cc", [])
    bcc = notification_obj.metadata.get("bcc", [])
    from_email = notification_obj.metadata.get("from") or md.get("from_email")

    # 3) Build and send the provider request. Replace this block with your
    #    provider's real API call / SDK usage.
    base_url = md.get("api_base_url", "https://api.example.com/v1").rstrip("/")
    endpoint = f"{base_url}/messages"
    headers = {
        "Authorization": f"Bearer {md.get('api_key')}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": {"email": from_email, "name": md.get("from_name", "")},
        "to": [{"email": e} for e in to],
        "cc": [{"email": e} for e in cc],
        "bcc": [{"email": e} for e in bcc],
        "subject": subject,
        "html": body,
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201, 202):
            status = "SUCCESS"
            response = {"message": "SUCCESS", "data": resp.json() if resp.content else {}}
        else:
            status = "FAILED"
            response = {"error": resp.text, "status_code": resp.status_code}
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        status = "FAILED"
        response = {"error": str(e)}

    # 4) Persist the outcome.
    notification_obj.status = status
    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    notification_obj.save()

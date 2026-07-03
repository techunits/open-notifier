import base64
import traceback
import requests
from celery import shared_task

from notifications.models import NotificationLog
from django.conf import settings

logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "api_base_url": "https://api.sendpulse.com",
  "client_id": "xxxxxxxxxxxxxxxxxxxxxx",
  "client_secret": "xxxxxxxxxxxxxxxxxxxxxx",
  "from_email": "no-reply@example.com",
  "from_name": "Example"
}

SendPulse authenticates with an OAuth2 client-credentials token, then posts the
message to /smtp/emails with the HTML body base64-encoded (as the API expects).
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
    body = notification_obj.metadata.get("body") or ""
    to = notification_obj.metadata.get("to", [])
    cc = notification_obj.metadata.get("cc", [])
    bcc = notification_obj.metadata.get("bcc", [])
    from_email = notification_obj.metadata.get("from") or md.get("from_email")

    base_url = md.get("api_base_url", "https://api.sendpulse.com").rstrip("/")

    try:
        # 1) obtain an access token
        token_resp = requests.post(
            f"{base_url}/oauth/access_token",
            json={
                "grant_type": "client_credentials",
                "client_id": md.get("client_id"),
                "client_secret": md.get("client_secret"),
            },
            timeout=30,
        )
        access_token = (token_resp.json() if token_resp.content else {}).get("access_token")
        if not access_token:
            raise Exception(f"Failed to obtain access token: {token_resp.text}")

        # 2) send the email
        email = {
            "subject": subject,
            "html": base64.b64encode(body.encode("utf-8")).decode("ascii"),
            "from": {"name": md.get("from_name", ""), "email": from_email},
            "to": [{"email": e} for e in to],
        }
        if cc:
            email["cc"] = [{"email": e} for e in cc]
        if bcc:
            email["bcc"] = [{"email": e} for e in bcc]

        resp = requests.post(
            f"{base_url}/smtp/emails",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"email": email},
            timeout=30,
        )
        result = resp.json() if resp.content else {}
        if resp.status_code == 200 and result.get("result"):
            status = "SUCCESS"
            response = {"message": "SUCCESS", "data": result}
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

from celery import shared_task

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage
from notifications.models import NotificationLog, Configuration

from django.conf import settings
import traceback
import requests


logger = settings.LOGGER

""" SAMPLE CONFIG
{
  "INTERAKT_BASE_URL": "https://api.interakt.ai/v1",
  "INTERAKT_API_TOKEN": "****************************************************"
}
"""


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
    addon_data = notification_obj.metadata.get("addon_data", {})
    addon_data = {} if addon_data is None else addon_data

    # processing traits
    # processed_traits: dict = {}
    # for key in addon_data.get("interakt_traits", []):
    #     val: str = notification_obj.metadata.get("payload", {}).get(key, None)
    #     if val is not None:
    #         processed_traits[key] = val
    processed_traits = notification_obj.metadata.get("payload", {})

    # initialize the SMTP connection params
    interakt_obj = InteraktNotification(config=config_obj.metadata)

    notification_obj.status = "FAILED"

    # Use Case: MISSING_TARGET_MOBILE_NUMBERS
    if len(notification_obj.metadata.get("to_numbers", [])) == 0:
        response = {
            "error": {
                "ref": "MISSING_TARGET_MOBILE_NUMBERS",
                "message": "Missing target mobile numbers"
            }
        }

    else:
        # Use Case: MISSING_INTERAKT_EVENT
        interakt_event = addon_data.get("interakt_event", None)
        if interakt_event is None:
            interakt_event = notification_obj.metadata.get("template_ref")
        
        for to_number in notification_obj.metadata.get("to_numbers", []):
            is_sent, response = interakt_obj.send_whatsapp_message(
                isd_code=to_number.get("isd_code"),
                mobile_number=to_number.get("number"),
                event=interakt_event,
                traits=processed_traits, 
            )

            if is_sent is True:
                notification_obj.status = "SUCCESS"            

    notification_obj.metadata.update({"response": response})
    logger.info(f"{config_obj} Status({notification_id}): {notification_obj.status}")
    logger.info(f"{config_obj} Response({notification_id}): {response}")
    notification_obj.save()


class InteraktNotification:
    def __init__(self, config):
        self.config = config
        self.headers = {
            "Authorization": f"Basic {self.config.get('INTERAKT_API_TOKEN')}",
            "Content-Type": "application/json",
        }

    def create_user(self, isd_code, mobile_number, traits=None):
        api_url = f"{self.config.get('INTERAKT_BASE_URL')}/public/track/users/"
        payload = {
            "phoneNumber": mobile_number,
            "countryCode": isd_code,
            # "traits": {"data": "var_02"},
        }

        response = requests.post(api_url, headers=self.headers, json=payload)

        if response.status_code in [200, 201, 202]:
            logger.debug(
                f"Created interakt user(+{isd_code}-{mobile_number}): {response.json()}"
            )
            return True, response.json()
        else:
            logger.error(
                f"Failed to create interakt user(+{isd_code}-{mobile_number}): {response.text}"
            )
            return False, response.text

    def send_whatsapp_message(self, isd_code, mobile_number, event, traits):
        api_url = f"{self.config.get('INTERAKT_BASE_URL')}/public/track/events/"
        is_created, user_response = self.create_user(
            isd_code=isd_code, mobile_number=mobile_number
        )

        if is_created is True:
            payload = {
                "phoneNumber": mobile_number,
                "countryCode": isd_code,
                "event": event,
                "traits": traits,
            }

            response = requests.post(api_url, headers=self.headers, json=payload)
            if response.status_code in [200, 201, 202]:
                logger.debug(
                    f"Sent message to user(+{isd_code}-{mobile_number}): {response.json()}"
                )
                return True, response.json()
            else:
                logger.error(
                    f"Failed to send message to user(+{isd_code}-{mobile_number}): {response.text}"
                )
                return False, response.text

        return is_created, user_response

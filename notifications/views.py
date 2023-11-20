from rest_framework import status
from django.conf import settings
from notifications.models import NotificationLog, Configuration
from notifications.serializers import NotificationLogSerializer
from rest_framework.response import Response
from notifications.validators import (
    NotificationURLValidatorView,
    NotificationPayloadValidator,
)
from notifier.validators.errors import ErrorResponseException

logger = settings.LOGGER

class NotificationView(NotificationURLValidatorView):
    def post(self, request, tenant_id):
        # request param validation
        self.validate_request_params(tenant_id=tenant_id)

        # payload validation
        payload = request.data
        logger.debug(f"Request payload: {payload}")
        validator = NotificationPayloadValidator(
            data=payload,
            context={
                "request": request,
                "tenant": self.tenant,
                "notification_type": payload.get("notification_type", None),
            },
        )
        validator.validate(required_fields=["template_ref"])

        notifications = []
        for validated_template in validator.templates:
            logger.debug(f"Requested template ref: {validated_template}")
            for notification_type in validated_template.notification_types:
                logger.debug(f"Computed notification type: {notification_type}")
                notification_ref = Configuration.objects.filter(
                    tenant=self.tenant,
                    notification_type=notification_type,
                    is_default=True,
                    is_enabled=True,
                    is_deleted=False,
                ).first()
                if notification_ref is None:
                    raise ErrorResponseException(
                        "NOTIFICATION_CONFIG_NOT_EXISTS",
                        f"Notification configuration does not exist for {notification_type}",
                        status.HTTP_400_BAD_REQUEST,
                    )

                # process payload if sent as list
                body_payload = dict()
                if type(payload.get('payload', [])) is list:
                    for item in payload.get('payload', []):
                        body_payload[item.get('key')] = item.get('value')
                else:
                    body_payload = payload.get('payload', {})

                validated_template.set_subject(payload=body_payload)
                validated_template.set_body(payload=body_payload)

                # schedule email template based notification
                logger.info(f"Scheduling notification task({notification_type}): ")
                notification_id = validated_template.schedule_notification(
                    tenant_id=self.tenant.id,
                    notification_ref=notification_ref,
                    metadata={
                        "payload": body_payload,
                        "to_numbers": payload.get('to_numbers', []),
                        "to": payload.get('to', []),
                        "cc": payload.get('cc', []),
                        "bcc": payload.get('bcc', []),
                    }
                )
                notifications.append({"id": notification_id})

        return Response({"notifications": notifications})

    def get(self, request, tenant_id):
        # request param validation
        self.validate_request_params(tenant_id=tenant_id)

        notifications = NotificationLog.objects.filter(
            notification_ref__tenant=self.tenant
        )
        return Response(
            {
                "notifications": NotificationLogSerializer(
                    notifications,
                    many=True,
                    context={
                        "request": request,
                    },
                ).data
            }
        )

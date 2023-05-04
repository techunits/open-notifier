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
        validator = NotificationPayloadValidator(
            data=payload,
            context={
                "request": request,
                "tenant": self.tenant,
                "notification_type": payload.get("notification_type", "EMAIL"),
            },
        )
        validator.validate(required_fields=["to", "template_ref"])
        
        notification_ref = Configuration.objects.filter(
            tenant=self.tenant,
            notification_type__in=validator.template.notification_types,
            is_default=True,
        ).first()
        if notification_ref is None:
            raise ErrorResponseException(
                "NOTIFICATION_CONFIG_NOT_EXISTS",
                "Notification configuration does not exist",
                status.HTTP_400_BAD_REQUEST,
            )

        # schedule email template based notification
        validator.template.set_subject(payload)
        validator.template.set_body(payload)
        notification_id = validator.template.schedule_notification(
            tenant_id=self.tenant.id,
            notification_ref=notification_ref,
            metadata=payload,
        )

        return Response({"notification": {"id": notification_id}})

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

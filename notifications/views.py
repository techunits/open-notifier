from notifications.models import NotificationLog
from notifications.serializers import NotificationLogSerializer
from rest_framework.response import Response
from notifications.validators import (
    NotificationURLValidatorView,
    NotificationPayloadValidator,
)


class NotificationView(NotificationURLValidatorView):
    def post(self, request, tenant_id):
        # request param validation
        self.validate_request_params(tenant_id=tenant_id)

        # payload validation
        payload = request.data
        validator = NotificationPayloadValidator(
            data=payload, context={"request": request, "tenant": self.tenant}
        )
        validator.validate(required_fields=["to", "template_ref"])

        # schedule email template based notification
        validator.template.set_subject(payload)
        validator.template.set_body(payload)
        notification_id = validator.template.schedule_notification(
            tenant_id=self.tenant.id, metadata=payload
        )

        return Response({"notification": {"id": notification_id}})

    def get(self, request, tenant_id):
        # request param validation
        self.validate_request_params(tenant_id=tenant_id)

        notifications = NotificationLog.objects.filter(tenant=self.tenant)
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


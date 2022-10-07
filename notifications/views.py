from importlib.metadata import metadata
from django.shortcuts import render

from templates.models import Template
from rest_framework.response import Response
from notifications.validators import (
    NotificationURLValidatorView,
    NotificationPayloadValidator
)


class NotificationView(NotificationURLValidatorView):
    def post(self, request):
        # payload validation
        payload = request.data
        validator = NotificationPayloadValidator(
            data=payload,
            context={
                "request": request,
            }
        )
        validator.validate(required_fields=[
            'to', 
            'template_ref'
        ])

        # schedule email template based notification
        validator.template.set_subject(payload)
        validator.template.set_body(payload)
        notification_id = validator.template.schedule_notification(metadata=payload)

        return Response({
            "notification": {
                "id": notification_id
            }
        })

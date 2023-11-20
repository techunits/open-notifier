from rest_framework import status
from django.conf import settings
from rest_framework.response import Response
from notifications.validators import (
    NotificationURLValidatorView,
)
from templates.models import Template
from templates.serializers import TemplateSerializer

logger = settings.LOGGER


class TemplateView(NotificationURLValidatorView):
    def get(self, request, tenant_id):
        # request param validation
        self.validate_request_params(tenant_id=tenant_id)

        templates = Template.objects.filter(
            tenant=self.tenant
        )
        return Response(
            {
                "templates": TemplateSerializer(
                    templates,
                    many=True,
                    context={
                        "request": request,
                    },
                ).data
            }
        )

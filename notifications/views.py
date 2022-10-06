from django.shortcuts import render

from .models import Configuration, NotificationLog
from templates.models import Template
from rest_framework.views import APIView
from rest_framework.response import Response

from .tasks import send_email_notification

import jinja2


class NotificationView(APIView):

    def post(self, request):

        # POST Request Payload
        data = request.data

        # Validate if Payload of html exists
        payload = data.get('payload')
        if not payload:
            return Response({
                "error":{
                    "message": "payload not found"
                }
            }, status=400)

        # Validate if template_ref exists
        template_ref = data.get('template_ref')
        if not template_ref:
            return Response({
                "error": {
                    "message": "template_ref not found"
                }
            }, status=400)

        # Validate template_ref
        try:
            template_obj = Template.objects.get(ref=template_ref)
        except Exception as e:
            return Response({
                "error": {
                    "message": "invalid template_ref"
                }
            }, status=400)

        # Embed payload with template
        html_body = template_obj.body
        environment = jinja2.Environment()
        template = environment.from_string(html_body)
        final_html = template.render(payload)

        # Insert final_html to the NotificationLog data
        data['html'] = final_html

        # Create Notification
        notificationlog_obj = NotificationLog()
        notificationlog_obj.metadata = data
        notificationlog_obj.save()

        # celery task with notification id
        send_email_notification.delay(notificationlog_obj.id)

        return Response({
            "notification": {
                "id": notificationlog_obj.id
            }
        })

from django.shortcuts import render

from .models import NotificationLog
from rest_framework.views import APIView
from rest_framework.response import Response

from .tasks import send_email_notification

class NotificationView(APIView):
    def post(self, request):
        data = request.data

        # Create Notification
        notificationlog_obj = NotificationLog()
        notificationlog_obj.metadata = data
        notificationlog_obj.save()



        send_email_notification.delay(notificationlog_obj.id)

        # TODO: create celery task with notification id

        return Response({
            "notification": {
                "id": notificationlog_obj.id
            }
        })

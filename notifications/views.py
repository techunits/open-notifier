from django.shortcuts import render

from .models import Configuration, NotificationLog
from rest_framework.views import APIView
from rest_framework.response import Response



class NotificationView(APIView):

    def post(self, request):

        data = request.data

        # Create Notification
        notificationlog_obj = NotificationLog()
        notificationlog_obj.metadata = data
        notificationlog_obj.save()

        # TODO: create celery task with notification id

        return Response({
            "notification": {
                "id": notificationlog_obj.id
            }
        })

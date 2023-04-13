from rest_framework import serializers
from notifications.models import NotificationLog

class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = '__all__'
    
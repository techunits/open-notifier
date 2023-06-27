from re import template
from django.db import models
from rest_framework import status
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField
from django.contrib.postgres.fields import ArrayField
from django.template import Template as DjangoTemplate, Context
from tenants.models import Tenant
from notifications.models import NOTIFICATION_TYPE_CHOICES
from notifier.validators.errors import ErrorResponseException


class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, related_name="templates", on_delete=models.CASCADE
    )
    notification_types = ArrayField(
        models.CharField(
            choices=NOTIFICATION_TYPE_CHOICES,
            max_length=50,
            blank=True,
            default="EMAIL",
        ),
        default=["EMAIL"],
    )
    name = models.CharField(max_length=255)
    ref = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    addon_data = models.JSONField(blank=True, null=True)
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(
        use_numeric=True, auto_now_add=True, default=timezone.now
    )
    modified_on = UnixTimeStampField(
        use_numeric=True, auto_now=True, default=timezone.now
    )
    created_by = models.UUIDField()
    modified_by = models.UUIDField()

    def __str__(self):
        return self.ref

    class Meta:
        db_table = "templates"

    def set_subject(self, payload={}):
        try:
            template = DjangoTemplate(self.subject)
            self.notification_subject = template.render(Context(payload))
        except Exception as e:
            raise ErrorResponseException(
                "NOTIFICATION_TEMPLATE_RENDER_ERROR",
                f"Notification template render error on subject: {e}",
                status.HTTP_400_BAD_REQUEST,
            )

    def set_body(self, payload={}):
        try:
            template = DjangoTemplate(self.body)
            self.notification_body = template.render(Context(payload))
        except Exception as e:
            raise ErrorResponseException(
                "NOTIFICATION_TEMPLATE_RENDER_ERROR",
                f"Notification template render error on body: {e}",
                status.HTTP_400_BAD_REQUEST,
            )

    def schedule_notification(self, tenant_id, notification_ref, metadata):
        # create notification enrtry
        from notifications.models import NotificationLog

        # set subject and body
        # print(self.notification_body)
        metadata["template_ref"] = self.ref
        metadata["addon_data"] = self.addon_data
        metadata["body"] = self.notification_body
        if metadata.get("subject", None) is None:
            metadata["subject"] = self.notification_subject

        notificationlog_obj = NotificationLog()
        notificationlog_obj.notification_ref = notification_ref
        notificationlog_obj.metadata = metadata
        notificationlog_obj.save()
        notification_id = str(notificationlog_obj.id)

        # schedule notification task
        from notifications.tasks import send_notification
        send_notification.delay(notification_id=notification_id)

        return notification_id

from re import template
from django.db import models
import uuid
from django.utils import timezone
from unixtimestampfield.fields import UnixTimeStampField
from django.template import Template as DjangoTemplate, Context
from tenants.models import Tenant


class Template(models.Model):
    id = models.UUIDField(
        primary_key = True, default = uuid.uuid4, editable = False
    )
    tenant = models.ForeignKey(Tenant, related_name='templates', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    ref = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_on = UnixTimeStampField(use_numeric=True, auto_now_add=True, default=timezone.now)
    modified_on = UnixTimeStampField(use_numeric=True, auto_now=True, default=timezone.now)
    created_by = models.UUIDField()
    modified_by = models.UUIDField()
    
    def __str__(self):
        return self.ref
    
    class Meta:
        db_table = 'templates'
    
    def set_subject(self, payload={}):
        template = DjangoTemplate(self.subject)
        self.notification_subject = template.render(Context(payload))

    def set_body(self, payload={}):
        template = DjangoTemplate(self.subject)
        self.notification_body = template.render(Context(payload))

    def schedule_notification(self, tenant_id, metadata):
        # create notification enrtry
        from notifications.models import NotificationLog
        notificationlog_obj = NotificationLog()
        notificationlog_obj.tenant_id = tenant_id
        notificationlog_obj.metadata = metadata
        notificationlog_obj.save()
        notification_id = str(notificationlog_obj.id)

        # schedule task
        from notifications.tasks import send_email_notification
        send_email_notification.delay(notification_id=notification_id)

        return notification_id


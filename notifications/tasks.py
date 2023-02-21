import traceback
from celery import shared_task

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage


from .models import (
    NotificationLog,
    Configuration
)


@shared_task
def send_email_notification(notification_id):
    # pull up notification details
    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception as e:
        print("notification entry not found")

    # pull up config details
    try:
        config_obj = Configuration.objects.get(
            notification_type="EMAIL", 
            provider="LOCAL_EMAIL"
        )
    except Exception as e:
        traceback.print_exc()
        print("MISSING_NOTIFICATION_CONFIG")
        notification_obj.status = 'FAILED'
        notification_obj.save()
        return False
    
    # initialize the SMTP connection params
    email_backend = EmailBackend(
        host=config_obj.metadata.get("smtp_host"),
        port=config_obj.metadata.get("smtp_port"),
        password=config_obj.metadata.get("smtp_password"),
        username=config_obj.metadata.get("smtp_username"),
        use_tls=config_obj.metadata.get("smtp_tls", False),
        fail_silently=False
    )
    
    subject = notification_obj.metadata.get('subject')
    body = notification_obj.metadata.get('html')

    from_email = notification_obj.metadata.get('from')
    if not from_email:
        from_email = config_obj.metadata.get("smtp_from_email", 'test@example.com')

    email_response = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=notification_obj.metadata.get('to', []),
        cc=notification_obj.metadata.get('cc', []),
        bcc=notification_obj.metadata.get('bcc', []),
        connection=email_backend
    )

    if email_response:
        notification_obj.status = 'SUCCESS'
    else:
        notification_obj.status = 'FAILED'

    print("Email: " + notification_obj.status)
    notification_obj.save()

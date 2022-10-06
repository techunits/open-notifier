import traceback
from django.conf import settings
from celery import shared_task
from django.core.mail import (
    BadHeaderError, 
    EmailMultiAlternatives
)

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import send_mail

from .models import (
    NotificationLog,
    Configuration
)

# @shared_task
# def send_email_notification(subject, body, to=[]):
#     from_email = settings.SMTP_DEFAULT_FROM_EMAIL
#     try:
#         msg = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=to)
#         msg.attach_alternative(body, "text/html")
#         resp = msg.send(fail_silently = False)
#         print('email sent successfully: ', resp)
#     except BadHeaderError as e:
#         traceback.print_exc()
#         print('email sending failed: ', e)

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
            config_type="EMAIL", 
            provider="LOCAL_EMAIL"
        )
    except Exception as e:
        print("notification configuration not found")
    

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

    recipient_list = notification_obj.metadata.get('to')
    if notification_obj.metadata.get('cc'):
        for email in notification_obj.metadata.get('cc'):
            recipient_list.append(email)
    if notification_obj.metadata.get('bcc'):
        for email in notification_obj.metadata.get('bcc'):
            recipient_list.append(email)

    from_email = notification_obj.metadata.get('from')
    if not from_email:
        from_email = config_obj.metadata.get("smtp_from_email")

    no_of_success = send_mail(
        subject=subject,
        message=body,
        from_email=from_email,
        recipient_list=recipient_list,
        connection=email_backend,
        html_message=body,
    )

    if no_of_success:
        notification_obj.status = 'SUCCESS'
    else:
        notification_obj.status = 'FAILED'
    notification_obj.save()

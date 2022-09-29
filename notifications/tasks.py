import traceback
from django.conf import settings
from celery import shared_task
from django.core.mail import (
    BadHeaderError, 
    EmailMultiAlternatives
)

from django.core.mail import send_mail

from .models import NotificationLog

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

    try:
        notification_obj = NotificationLog.objects.get(id=notification_id)
    except Exception as e:
        print("notification log not found")

    print(notification_obj)

    subject = notification_obj.metadata.get('subject')
    body = "TEST"
    recipient_list = notification_obj.metadata.get('to')

    from_email = '2012shubho@gmail.com'

    no_of_success = send_mail(
        subject=subject,
        message=body,
        from_email=from_email,
        recipient_list=recipient_list,
        auth_user=from_email,
        auth_password='19561956d!',
        html_message=None,
    )

    if no_of_success:
        notification_obj.status = 'SUCCESS'
    else:
        notification_obj.status = 'FAILED'
    notification_obj.save()
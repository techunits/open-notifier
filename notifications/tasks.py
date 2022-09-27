import traceback
from django.conf import settings
from celery import shared_task
from django.core.mail import (
    BadHeaderError, 
    EmailMultiAlternatives
)

@shared_task
def send_email_notification(subject, body, to=[]):
    from_email = settings.SMTP_DEFAULT_FROM_EMAIL
    try:
        msg = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=to)
        msg.attach_alternative(body, "text/html")
        resp = msg.send(fail_silently = False)
        print('email sent successfully: ', resp)
    except BadHeaderError as e:
        traceback.print_exc()
        print('email sending failed: ', e)


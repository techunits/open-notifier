from django.conf import settings


def console(request):
    """Expose console-wide flags to every template."""
    return {
        "disable_email_sending": getattr(settings, "DISABLE_EMAIL_SENDING", False),
    }

# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in celery/SMTP deps.

# Sky-blue "SMTP" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#0EA5E9"/>'
    '<text x="12" y="15.5" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="6" font-weight="700" fill="#ffffff">SMTP</text></svg>'
)

# Integration manifest used by the admin panel to discover this provider and
# render the correct configuration form. `provider` must match a value in
# notifications.models.PROVIDER_STATUS_CHOICES and the lowercased value must
# match this package directory name (see notifications/tasks.py).
MANIFEST = {
    "key": "smtp_email",
    "provider": "SMTP_EMAIL",
    "name": "SMTP Email",
    "notification_type": "EMAIL",
    "description": "Sends transactional emails through any standard SMTP server "
    "using Django's email backend.",
    "brand_color": "#0EA5E9",
    "logo": LOGO,
    "config_fields": [
        {"name": "smtp_host", "label": "SMTP Host", "type": "host", "required": True,
         "placeholder": "smtp.example.com"},
        {"name": "smtp_port", "label": "SMTP Port", "type": "number", "required": True,
         "default": 25, "min": 1, "max": 65535},
        {"name": "smtp_username", "label": "SMTP Username", "type": "text", "required": True,
         "placeholder": "webmaster@example.com"},
        {"name": "smtp_password", "label": "SMTP Password", "type": "password", "required": True,
         "secret": True},
        {"name": "smtp_tls", "label": "Use TLS", "type": "boolean", "default": True},
        {"name": "smtp_from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "webmaster@example.com"},
    ],
}

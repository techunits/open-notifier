# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# SendGrid blue "SG" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#1A82E2"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">SG</text></svg>'
)

MANIFEST = {
    "key": "sendgrid",
    "provider": "SENDGRID",
    "name": "SendGrid",
    "notification_type": "EMAIL",
    "description": "Sends email through the SendGrid v3 Mail Send API.",
    "brand_color": "#1A82E2",
    "logo": LOGO,
    "config_fields": [
        {"name": "api_key", "label": "API Key", "type": "password", "required": True,
         "secret": True, "pattern": r"^SG\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}$",
         "pattern_message": "API Key must look like a SendGrid key (SG.xxxx.yyyy)."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://api.sendgrid.com/v3"},
    ],
}

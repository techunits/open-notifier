# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# SendPulse blue "SP" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#12A5F4"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">SP</text></svg>'
)

MANIFEST = {
    "key": "sendpulse",
    "provider": "SENDPULSE",
    "name": "SendPulse",
    "notification_type": "EMAIL",
    "description": "Sends email through the SendPulse SMTP API (OAuth2 client credentials).",
    "brand_color": "#12A5F4",
    "logo": LOGO,
    "config_fields": [
        {"name": "client_id", "label": "Client ID (API User ID)", "type": "text", "required": True,
         "pattern": r"^[A-Za-z0-9]{16,}$",
         "pattern_message": "Client ID must be at least 16 alphanumeric characters."},
        {"name": "client_secret", "label": "Client Secret", "type": "password", "required": True,
         "secret": True, "pattern": r"^[A-Za-z0-9]{16,}$",
         "pattern_message": "Client Secret must be at least 16 alphanumeric characters."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://api.sendpulse.com"},
    ],
}

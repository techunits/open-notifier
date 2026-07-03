# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# Mailtrap indigo "MT" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#5B4FE0"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">MT</text></svg>'
)

MANIFEST = {
    "key": "mailtrap",
    "provider": "MAILTRAP",
    "name": "Mailtrap",
    "notification_type": "EMAIL",
    "description": "Sends email through the Mailtrap Email Sending API.",
    "brand_color": "#5B4FE0",
    "logo": LOGO,
    "config_fields": [
        {"name": "api_token", "label": "API Token", "type": "password", "required": True,
         "secret": True, "pattern": r"^[A-Za-z0-9]{16,}$",
         "pattern_message": "API Token must be at least 16 alphanumeric characters."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://send.api.mailtrap.io"},
    ],
}

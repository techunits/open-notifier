# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# Elastic Email blue "EE" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#2F6FED"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">EE</text></svg>'
)

MANIFEST = {
    "key": "elastic_email",
    "provider": "ELASTIC_EMAIL",
    "name": "Elastic Email",
    "notification_type": "EMAIL",
    "description": "Sends email through the Elastic Email v2 HTTP API.",
    "brand_color": "#2F6FED",
    "logo": LOGO,
    "config_fields": [
        {"name": "api_key", "label": "API Key", "type": "password", "required": True,
         "secret": True, "pattern": r"^[A-Za-z0-9\-]{16,}$",
         "pattern_message": "API Key must be at least 16 characters (letters, digits, dashes)."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://api.elasticemail.com/v2"},
    ],
}

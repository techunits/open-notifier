# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# Postmark yellow "PM" badge (dark text on Postmark yellow).
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#FFCB00"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#12344D">PM</text></svg>'
)

MANIFEST = {
    "key": "postmark",
    "provider": "POSTMARK",
    "name": "Postmark",
    "notification_type": "EMAIL",
    "description": "Sends transactional email through the Postmark Email API.",
    "brand_color": "#FFCB00",
    "logo": LOGO,
    "config_fields": [
        {"name": "server_token", "label": "Server Token", "type": "password", "required": True,
         "secret": True, "pattern": r"^[0-9a-fA-F\-]{16,}$",
         "pattern_message": "Server Token must be at least 16 characters (usually a UUID)."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "message_stream", "label": "Message Stream", "type": "text", "required": False,
         "default": "outbound"},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://api.postmarkapp.com"},
    ],
}

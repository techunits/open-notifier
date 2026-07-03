# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# Mailchimp yellow "MC" badge (dark text on Cavendish yellow).
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#FFE01B"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#241C15">MC</text></svg>'
)

MANIFEST = {
    "key": "mailchimp",
    "provider": "MAILCHIMP",
    "name": "Mailchimp",
    "notification_type": "EMAIL",
    "description": "Sends transactional email through the Mailchimp Transactional "
    "(Mandrill) messages API.",
    "brand_color": "#FFE01B",
    "logo": LOGO,
    "config_fields": [
        {"name": "api_key", "label": "API Key", "type": "password", "required": True,
         "secret": True, "pattern": r"^[A-Za-z0-9_\-]{16,}$",
         "pattern_message": "API Key must be at least 16 characters."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://mandrillapp.com/api/1.0"},
    ],
}

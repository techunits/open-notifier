# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in requests/celery.

# WhatsApp-green "IK" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#25D366"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">IK</text></svg>'
)

# Integration manifest used by the admin panel to discover this provider and
# render the correct configuration form. `provider` must match a value in
# notifications.models.PROVIDER_STATUS_CHOICES and the lowercased value must
# match this package directory name (see notifications/tasks.py).
MANIFEST = {
    "key": "interakt",
    "provider": "INTERAKT",
    "name": "Interakt (WhatsApp)",
    "notification_type": "WHATSAPP",
    "description": "Sends WhatsApp template messages through the Interakt Business API.",
    "brand_color": "#25D366",
    "logo": LOGO,
    "config_fields": [
        {"name": "INTERAKT_BASE_URL", "label": "Base URL", "type": "url", "required": True,
         "default": "https://api.interakt.ai/v1"},
        {"name": "INTERAKT_API_TOKEN", "label": "API Token", "type": "password", "required": True,
         "secret": True},
    ],
}

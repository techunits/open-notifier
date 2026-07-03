# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in celery/SMTP deps.

# Simple slate "PF" (Postfix) badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#334155"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">PF</text></svg>'
)

MANIFEST = {
    "key": "local_email",
    "provider": "LOCAL_EMAIL",
    "name": "Local Email (Postfix)",
    "notification_type": "EMAIL",
    "description": "Hands messages straight to the local Postfix / MTA on this host "
    "(127.0.0.1:25, no authentication) — no SMTP settings required, only the sender address.",
    "brand_color": "#334155",
    "logo": LOGO,
    # The local MTA is reached directly on 127.0.0.1:25 with no auth/TLS, so the
    # only thing to configure is the From address.
    "config_fields": [
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
    ],
}

# =============================================================================
# BOILERPLATE — copy this package to add a new email provider.
#
# Steps:
#   1. Copy the `sample_email/` directory to `notifications/integrations/<key>/`
#      where <key> is your provider's lowercase directory name (e.g. `postal`).
#      The lowercased `provider` MUST equal the directory <key> (that's how
#      tasks.py finds it). No model edit or migration is needed — provider
#      choices are auto-discovered from this directory at startup.
#   2. Fill in the MANIFEST below and implement send() in sender.py.
#   3. Restart the app, then enable the provider on the console Integrations
#      page (new providers are disabled by default).
#
# NOTE: this __init__ is imported just to read MANIFEST/LOGO — keep it free of
# heavy imports (requests, boto3, SMTP, …). Those belong in sender.py, which is
# imported lazily at send time.
# =============================================================================

# Inline SVG badge shown in the console (optional). Keep it a small square.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#64748B"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="9" font-weight="700" fill="#ffffff">SM</text></svg>'
)

MANIFEST = {
    "key": "sample_email",            # must match this directory name
    "provider": "SAMPLE_EMAIL",       # UPPERCASE; must be in PROVIDER_STATUS_CHOICES
    "name": "Sample Email (template)",
    "notification_type": "EMAIL",      # EMAIL | WHATSAPP | SMS
    "description": "Boilerplate email provider. Copy this package to build a real one.",
    "brand_color": "#64748B",
    "logo": LOGO,
    # config_fields drives the console Configuration form and is validated both
    # in the browser and on the server (en_console/metadata.py).
    #   type: text | host | url | number | password | email | boolean
    #   extra keys: required, default, placeholder, secret, min/max (number),
    #               pattern + pattern_message (regex format)
    "config_fields": [
        {"name": "api_key", "label": "API Key", "type": "password", "required": True,
         "secret": True},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
        {"name": "from_name", "label": "From Name", "type": "text", "required": False},
        {"name": "api_base_url", "label": "API Base URL", "type": "url", "required": True,
         "default": "https://api.example.com/v1"},
    ],
}

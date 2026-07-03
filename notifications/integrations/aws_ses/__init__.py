# NOTE: the delivery worker in ./sender.py is imported lazily (by
# notifications.tasks), so reading this manifest never pulls in boto3/celery.

# AWS orange "SES" badge.
LOGO = (
    '<svg viewBox="0 0 24 24" width="24" height="24" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="24" height="24" rx="5" fill="#FF9900"/>'
    '<text x="12" y="16" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" '
    'font-size="7" font-weight="700" fill="#232F3E">SES</text></svg>'
)

MANIFEST = {
    "key": "aws_ses",
    "provider": "AWS_SES",
    "name": "AWS SES",
    "notification_type": "EMAIL",
    "description": "Sends email through the Amazon SES API (requires the boto3 package).",
    "brand_color": "#FF9900",
    "logo": LOGO,
    "config_fields": [
        {"name": "aws_access_key_id", "label": "Access Key ID", "type": "text", "required": True,
         "pattern": r"^(AKIA|ASIA)[0-9A-Z]{16}$",
         "pattern_message": "Access Key ID must be 20 characters starting with AKIA/ASIA."},
        {"name": "aws_secret_access_key", "label": "Secret Access Key", "type": "password",
         "required": True, "secret": True, "pattern": r"^.{40}$",
         "pattern_message": "Secret Access Key must be 40 characters."},
        {"name": "aws_region", "label": "Region", "type": "text", "required": True,
         "default": "us-east-1", "pattern": r"^[a-z]{2}-[a-z]+-\d$",
         "pattern_message": "Region must look like us-east-1."},
        {"name": "from_email", "label": "From Email", "type": "email", "required": True,
         "placeholder": "no-reply@example.com"},
    ],
}

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0009_alter_configuration_provider"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuration",
            name="provider",
            field=models.CharField(
                choices=[
                    ("SMTP_EMAIL", "SMTP_EMAIL"),
                    ("LOCAL_EMAIL", "LOCAL_EMAIL"),
                    ("SENDGRID", "SENDGRID"),
                    ("ELASTIC_EMAIL", "ELASTIC_EMAIL"),
                    ("MAILCHIMP", "MAILCHIMP"),
                    ("AWS_SES", "AWS_SES"),
                    ("INTERAKT", "INTERAKT"),
                ],
                default="SMTP_EMAIL",
                max_length=100,
            ),
        ),
    ]

from django.db import migrations, models


def rename_local_email(apps, schema_editor):
    """Migrate any legacy LOCAL_EMAIL configurations to the SMTP_EMAIL provider."""
    Configuration = apps.get_model("notifications", "Configuration")
    Configuration.objects.filter(provider="LOCAL_EMAIL").update(provider="SMTP_EMAIL")


def reverse_rename(apps, schema_editor):
    Configuration = apps.get_model("notifications", "Configuration")
    Configuration.objects.filter(provider="SMTP_EMAIL").update(provider="LOCAL_EMAIL")


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0008_alter_notificationlog_status"),
    ]

    operations = [
        migrations.RunPython(rename_local_email, reverse_rename),
        migrations.AlterField(
            model_name="configuration",
            name="provider",
            field=models.CharField(
                choices=[("SMTP_EMAIL", "SMTP_EMAIL"), ("INTERAKT", "INTERAKT")],
                default="SMTP_EMAIL",
                max_length=100,
            ),
        ),
    ]

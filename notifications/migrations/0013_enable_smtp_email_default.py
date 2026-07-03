from django.db import migrations


def enable_smtp_email(apps, schema_editor):
    """Seed SMTP_EMAIL as enabled by default (all other providers stay disabled).

    Uses get_or_create so it never clobbers an existing choice — after this
    one-time seed the provider is fully user-controlled from the console.
    """
    IntegrationState = apps.get_model("notifications", "IntegrationState")
    IntegrationState.objects.get_or_create(
        provider="SMTP_EMAIL", defaults={"is_enabled": True}
    )


def noop(apps, schema_editor):
    # Don't undo a user's toggle on reverse.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0012_integrationstate_alter_configuration_provider"),
    ]

    operations = [
        migrations.RunPython(enable_smtp_email, noop),
    ]

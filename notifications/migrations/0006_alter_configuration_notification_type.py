# Generated by Django 4.1.7 on 2023-05-04 06:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0005_configuration_is_default"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuration",
            name="notification_type",
            field=models.CharField(
                choices=[("EMAIL", "EMAIL"), ("WHATSAPP", "WHATSAPP")],
                default="EMAIL",
                max_length=100,
            ),
        ),
    ]
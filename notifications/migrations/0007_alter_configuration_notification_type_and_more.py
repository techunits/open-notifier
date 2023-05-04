# Generated by Django 4.1.7 on 2023-05-04 08:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0006_alter_configuration_notification_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuration",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("EMAIL", "EMAIL"),
                    ("WHATSAPP", "WHATSAPP"),
                    ("SMS", "SMS"),
                ],
                default="EMAIL",
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="configuration",
            name="provider",
            field=models.CharField(
                choices=[("LOCAL_EMAIL", "LOCAL_EMAIL"), ("INTERAKT", "INTERAKT")],
                default="LOCAL_EMAIL",
                max_length=100,
            ),
        ),
    ]
# Generated by Django 4.1.6 on 2023-02-21 05:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("templates", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="template",
            name="notification_type",
            field=models.CharField(
                choices=[("EMAIL", "EMAIL")], default="EMAIL", max_length=50
            ),
        ),
    ]

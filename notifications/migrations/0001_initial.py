# Generated by Django 4.1.1 on 2022-10-07 06:34

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import unixtimestampfield.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('notification_type', models.CharField(choices=[('EMAIL', 'EMAIL')], default='EMAIL', max_length=100)),
                ('status', models.CharField(choices=[('QUEUED', 'QUEUED'), ('SUCCESS', 'SUCCESS'), ('FAILED', 'FAILED')], default='QUEUED', max_length=100)),
                ('metadata', models.JSONField()),
                ('created_on', unixtimestampfield.fields.UnixTimeStampField(auto_now_add=True, default=django.utils.timezone.now)),
                ('modified_on', unixtimestampfield.fields.UnixTimeStampField(auto_now=True, default=django.utils.timezone.now)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('modified_by', models.UUIDField(blank=True, null=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_logs', to='tenants.tenant')),
            ],
            options={
                'db_table': 'notification_logs',
            },
        ),
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('config_type', models.CharField(choices=[('EMAIL', 'EMAIL')], default='EMAIL', max_length=100)),
                ('provider', models.CharField(blank=True, max_length=100, null=True)),
                ('metadata', models.JSONField()),
                ('is_enabled', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_on', unixtimestampfield.fields.UnixTimeStampField(auto_now_add=True, default=django.utils.timezone.now)),
                ('modified_on', unixtimestampfield.fields.UnixTimeStampField(auto_now=True, default=django.utils.timezone.now)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('modified_by', models.UUIDField(blank=True, null=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='configurations', to='tenants.tenant')),
            ],
            options={
                'db_table': 'configurations',
            },
        ),
    ]

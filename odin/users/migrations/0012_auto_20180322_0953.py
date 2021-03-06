# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-22 09:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_passwordreset'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('voided_at', models.DateTimeField(blank=True, null=True)),
                ('token', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='passwordreset',
            name='user',
        ),
        migrations.DeleteModel(
            name='PasswordReset',
        ),
    ]

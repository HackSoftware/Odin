# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-25 09:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0008_auto_20170719_1312'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='hidden',
        ),
        migrations.AddField(
            model_name='course',
            name='public',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-03-23 13:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0018_auto_20180201_0950'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='week',
            options={'ordering': ('number',)},
        ),
        migrations.AddField(
            model_name='includedmaterial',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='included_materials', to='education.Course'),
        ),
        migrations.AddField(
            model_name='includedmaterial',
            name='week',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='education.Week'),
        ),
        migrations.AddField(
            model_name='includedtask',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='included_tasks', to='education.Course'),
        ),
        migrations.AddField(
            model_name='includedtask',
            name='week',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='included_tasks', to='education.Week'),
        ),
        migrations.AlterField(
            model_name='week',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='weeks', to='education.Course'),
        ),
        migrations.AlterUniqueTogether(
            name='includedmaterial',
            unique_together=set([('week', 'material')]),
        ),
        migrations.AlterUniqueTogether(
            name='includedtask',
            unique_together=set([('week', 'task')]),
        ),
    ]

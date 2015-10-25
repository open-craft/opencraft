# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0033_auto_20151004_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='ansible_settings',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='progress',
            field=models.CharField(max_length=7, default='running', choices=[('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')]),
        ),
    ]

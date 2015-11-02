# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0034_auto_20151022_1652'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='mongo_pass',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='mongo_provisioned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='mongo_user',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='mysql_pass',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='mysql_provisioned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='mysql_user',
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='use_ephemeral_databases',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]

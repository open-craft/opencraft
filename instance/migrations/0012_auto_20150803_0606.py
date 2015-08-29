# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0011_auto_20150628_0810'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instancelogentry',
            name='level',
            field=models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('exception', 'Exception')], max_length=9, db_index=True, default='info'),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='level',
            field=models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('exception', 'Exception')], max_length=9, db_index=True, default='info'),
        ),
    ]

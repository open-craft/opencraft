# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def warn_to_warning(apps, schema_editor):
    InstanceLogEntry = apps.get_model('instance', 'InstanceLogEntry')
    ServerLogEntry = apps.get_model('instance', 'ServerLogEntry')
    for log_entry_model in (InstanceLogEntry, ServerLogEntry):
        log_entry_model.objects.filter(level='warn').update(level='warning')


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0026_auto_20150920_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generallogentry',
            name='level',
            field=models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], db_index=True, max_length=9, default='info'),
        ),
        migrations.AlterField(
            model_name='instancelogentry',
            name='level',
            field=models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], db_index=True, max_length=9, default='info'),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='level',
            field=models.CharField(choices=[('debug', 'Debug'), ('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], db_index=True, max_length=9, default='info'),
        ),
        migrations.RunPython(warn_to_warning),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def exception_to_critical(apps, schema_editor):
    InstanceLogEntry = apps.get_model('instance', 'InstanceLogEntry')
    ServerLogEntry = apps.get_model('instance', 'ServerLogEntry')
    for log_entry_model in (InstanceLogEntry, ServerLogEntry):
        log_entry_model.objects.filter(level='exception').update(level='critical')


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0025_auto_20150920_0907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generallogentry',
            name='level',
            field=models.CharField(max_length=9, db_index=True, default='info', choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('critical', 'Critical')]),
        ),
        migrations.AlterField(
            model_name='instancelogentry',
            name='level',
            field=models.CharField(max_length=9, db_index=True, default='info', choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('critical', 'Critical')]),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='level',
            field=models.CharField(max_length=9, db_index=True, default='info', choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('critical', 'Critical')]),
        ),
        migrations.RunPython(exception_to_critical),
    ]

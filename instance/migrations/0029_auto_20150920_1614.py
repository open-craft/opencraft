# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def level_uppercase(apps, schema_editor):
    InstanceLogEntry = apps.get_model('instance', 'InstanceLogEntry')
    ServerLogEntry = apps.get_model('instance', 'ServerLogEntry')
    GeneralLogEntry = apps.get_model('instance', 'GeneralLogEntry')
    for log_entry_model in (GeneralLogEntry, InstanceLogEntry, ServerLogEntry):
        for level_name in ('debug', 'info', 'warning', 'error', 'critical'):
            log_entry_model.objects.filter(level=level_name).update(level=level_name.upper())


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0028_log_entry_field_rename'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generallogentry',
            name='level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], max_length=9, db_index=True, default='info'),
        ),
        migrations.AlterField(
            model_name='instancelogentry',
            name='level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], max_length=9, db_index=True, default='info'),
        ),
        migrations.AlterField(
            model_name='instancelogentry',
            name='obj',
            field=models.ForeignKey(to='instance.OpenEdXInstance', related_name='log_entry_set'),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], max_length=9, db_index=True, default='info'),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='obj',
            field=models.ForeignKey(to='instance.OpenStackServer', related_name='log_entry_set'),
        ),
        migrations.RunPython(level_uppercase),
    ]

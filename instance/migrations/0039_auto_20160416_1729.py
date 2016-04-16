# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0038_merge'),
    ]

    operations = [
        migrations.RenameField(
            model_name='openstackserver',
            old_name='progress',
            new_name='_progress',
        ),
        migrations.RenameField(
            model_name='openstackserver',
            old_name='status',
            new_name='_status',
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='_progress',
            field=models.CharField(choices=[('failed', 'type'), ('running', 'type'), ('success', 'type')], default='running', db_column='progress', max_length=7),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='_status',
            field=models.CharField(choices=[('active', 'type'), ('booted', 'type'), ('new', 'type'), ('provisioning', 'type'), ('ready', 'type'), ('rebooting', 'type'), ('started', 'type'), ('terminated', 'type')], default='new', db_column='status', max_length=20, db_index=True),
        ),
        migrations.AlterField(
            model_name='generallogentry',
            name='level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], default='INFO', max_length=9, db_index=True),
        ),
        migrations.AlterField(
            model_name='instancelogentry',
            name='level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], default='INFO', max_length=9, db_index=True),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='level',
            field=models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], default='INFO', max_length=9, db_index=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0032_auto_20151002_2203'),
    ]

    operations = [
        migrations.AddField(
            model_name='openstackserver',
            name='progress',
            field=models.CharField(choices=[('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], max_length=7, default='success'),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='status',
            field=models.CharField(choices=[('new', 'New - Not yet loaded'), ('started', 'Started - Running but not active yet'), ('active', 'Active - Running but not booted yet'), ('booted', 'Booted - Booted but not ready to be added to the application'), ('provisioning', 'Provisioning - Provisioning is in progress'), ('rebooting', 'Rebooting - Reboot in progress, to apply changes from provisioning'), ('ready', 'Ready - Rebooted and ready to add to the application'), ('live', 'Live - Is actively used in the application and/or accessed by users'), ('stopping', 'Stopping - Stopping temporarily'), ('stopped', 'Stopped - Stopped temporarily'), ('terminating', 'Terminating - Stopping forever'), ('terminated', 'Terminated - Stopped forever')], max_length=20, db_index=True, default='new'),
        ),
        migrations.RunSQL(
            ["UPDATE instance_openstackserver SET status = 'provisioning' WHERE status = 'provisioned'"],
            ["UPDATE instance_openstackserver SET status = 'provisioned' WHERE status = 'provisioning'"],
        )
    ]

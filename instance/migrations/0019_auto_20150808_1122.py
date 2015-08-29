# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0018_auto_20150808_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openstackserver',
            name='status',
            field=models.CharField(default='new', choices=[('new', 'New - Not yet loaded'), ('started', 'Started - Running but not active yet'), ('active', 'Active - Running but not booted yet'), ('booted', 'Booted - Booted but not ready to be added to the application'), ('provisioned', 'Provisioned - Provisioning is completed'), ('rebooting', 'Rebooting - Reboot in progress, to apply changes from provisioning'), ('ready', 'Ready - Rebooted and ready to add to the application'), ('live', 'Live - Is actively used in the application and/or accessed by users'), ('stopping', 'Stopping - Stopping temporarily'), ('stopped', 'Stopped - Stopped temporarily'), ('terminating', 'Terminating - Stopping forever'), ('terminated', 'Terminated - Stopped forever')], max_length=11, db_index=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0014_auto_20150806_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='last_provisioning_started',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='status',
            field=models.CharField(choices=[('new', 'New - Not yet loaded'), ('started', 'Started - Running but not active yet'), ('active', 'Active - Running but not booted yet'), ('booted', 'Booted - Booted but not ready to be added to the application'), ('provisioned', 'Provisioned - Provisioning is completed, ready to add to the application'), ('live', 'Live - Is actively used in the application and/or accessed by users'), ('stopping', 'Stopping - Stopping temporarily'), ('stopped', 'Stopped - Stopped temporarily'), ('terminating', 'Terminating - Stopping forever'), ('terminated', 'Terminated - Stopped forever')], default='new', db_index=True, max_length=10),
        ),
    ]

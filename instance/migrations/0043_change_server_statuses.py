# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0042_add_instance_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openstackserver',
            name='_status',
            field=models.CharField(choices=[('booting', 'Booting'), ('building', 'Building'), ('failed', 'BuildFailed'), ('pending', 'Pending'), ('ready', 'Ready'), ('terminated', 'Terminated'), ('unknown', 'Unknown')], default='pending', db_column='status', max_length=20, db_index=True),
        ),
        migrations.RunSQL(
            [
                "UPDATE instance_openstackserver SET status = 'pending' WHERE status = 'new'",
                "UPDATE instance_openstackserver SET status = 'building' WHERE status = 'started'",
                "UPDATE instance_openstackserver SET status = 'booting' WHERE status = 'active' OR status = 'rebooting'",
                "UPDATE instance_openstackserver SET status = 'ready' WHERE status = 'booted' OR status = 'provisioning'",
            ],
        )
    ]

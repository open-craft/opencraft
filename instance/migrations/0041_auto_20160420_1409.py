# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0040_auto_20160420_0754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openstackserver',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('building', 'Building'), ('booting', 'Booting'), ('ready', 'Ready'), ('terminated', 'Terminated'), ('unknown', 'Unknown'), ('failed', 'BuildFailed')], max_length=20, db_index=True, default='pending'),
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

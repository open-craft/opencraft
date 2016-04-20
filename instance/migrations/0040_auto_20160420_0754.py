# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0039_auto_20160419_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlevmopenedxinstance',
            name='status',
            field=models.CharField(choices=[('terminated', 'Terminated'), ('configuring', 'ConfiguringServer'), ('failed', 'ConfigurationFailed'), ('waiting', 'WaitingForServer'), ('new', 'New'), ('running', 'Running'), ('error', 'Error')], default='new', max_length=20, db_index=True)
        )
    ]

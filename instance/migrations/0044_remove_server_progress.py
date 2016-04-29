# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0043_change_server_statuses'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='openstackserver',
            name='_progress',
        ),
    ]

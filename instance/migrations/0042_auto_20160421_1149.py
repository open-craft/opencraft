# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0041_auto_20160420_1409'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='openstackserver',
            name='progress',
        ),
    ]

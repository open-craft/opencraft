# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0008_auto_20150607_0802'),
    ]

    operations = [
        migrations.RenameField(
            model_name='openedxinstance',
            old_name='ansible_playbook',
            new_name='ansible_playbook_name',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0012_auto_20150803_0606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='commit_id',
            field=models.CharField(max_length=40, validators=[django.core.validators.RegexValidator(message='Full SHA1 hash required', regex='^[0-9a-f]{40}$')]),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='openstack_id',
            field=models.CharField(max_length=250, blank=True, db_index=True),
        ),
    ]

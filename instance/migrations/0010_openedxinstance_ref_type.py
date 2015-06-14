# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0009_auto_20150607_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='ref_type',
            field=models.CharField(max_length=50, default='heads'),
        ),
    ]

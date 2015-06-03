# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0004_auto_20150603_1824'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='commit_id',
            field=models.CharField(max_length=40),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0029_auto_20150920_1614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='base_domain',
            field=models.CharField(max_length=50, blank=True),
        ),
    ]

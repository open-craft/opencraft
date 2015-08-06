# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0013_auto_20150805_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instancelogentry',
            name='text',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='text',
            field=models.TextField(blank=True),
        ),
    ]

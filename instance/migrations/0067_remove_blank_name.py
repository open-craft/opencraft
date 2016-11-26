# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0066_populate_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mongodbserver',
            name='name',
            field=models.CharField(max_length=250, blank=False),
        ),
        migrations.AlterField(
            model_name='mysqlserver',
            name='name',
            field=models.CharField(max_length=250, blank=False),
        ),
    ]

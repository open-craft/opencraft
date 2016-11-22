# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0064_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='mongodbserver',
            name='description',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='mongodbserver',
            name='name',
            field=models.CharField(max_length=250, blank=True),
        ),
        migrations.AddField(
            model_name='mysqlserver',
            name='description',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AddField(
            model_name='mysqlserver',
            name='name',
            field=models.CharField(max_length=250, blank=True),
        ),
    ]

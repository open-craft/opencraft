# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0007_openedxinstance_ansible_extra_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='s3_access_key',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='s3_bucket_name',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='s3_secret_access_key',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]

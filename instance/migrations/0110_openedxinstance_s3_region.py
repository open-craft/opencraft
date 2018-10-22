# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-10-22 10:08
from __future__ import unicode_literals

from django.db import migrations, models
import functools
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0109_remove_github_admin_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='s3_region',
            field=models.CharField(blank=True, default=functools.partial(instance.models.utils._get_setting, *('AWS_S3_DEFAULT_REGION',), **{}), help_text='The region must support Signature Version 2. See https://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region for options. When set empty, the bucket is created in the default region us-east-1.', max_length=50),
        ),
    ]

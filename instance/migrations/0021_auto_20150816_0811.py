# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0020_auto_20150812_0750'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='certs_version',
            field=models.CharField(default='master', max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='configuration_version',
            field=models.CharField(default='master', max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='forum_version',
            field=models.CharField(default='master', max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='notifier_version',
            field=models.CharField(default='master', max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='xqueue_version',
            field=models.CharField(default='master', max_length=50),
        ),
    ]

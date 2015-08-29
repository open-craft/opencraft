# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0003_auto_20150531_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='ansible_playbook',
            field=models.CharField(max_length=50, default='edx_sandbox'),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='name',
            field=models.CharField(max_length=250),
        ),
    ]

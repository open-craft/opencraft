# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0022_auto_20150818_0605'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='ansible_source_repo_url',
            field=models.URLField(default='https://github.com/edx/configuration.git', max_length=256),
        ),
    ]

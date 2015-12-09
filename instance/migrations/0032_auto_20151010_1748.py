# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0031_openedxinstance_github_pr_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='theme_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='theme_name',
            field=models.CharField(default='default', max_length=50),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='theme_source_repo',
            field=models.CharField(blank='https://github.com/eeue56/edx-theme.git', max_length=256),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='theme_version',
            field=models.CharField(default='master', max_length=50),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0031_openedxinstance_github_pr_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='attempts',
            field=models.SmallIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0031_openedxinstance_github_pr_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='continuously_provisioned',
            field=models.BooleanField(default=False),
        ),
    ]

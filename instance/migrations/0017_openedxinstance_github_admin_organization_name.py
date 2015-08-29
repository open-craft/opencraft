# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0016_auto_20150807_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='github_admin_organization_name',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]

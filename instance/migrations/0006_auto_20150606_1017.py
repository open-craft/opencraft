# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0005_auto_20150603_1936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='base_domain',
            field=models.CharField(default='opencraft.com', max_length=50),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_organization_name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_repository_name',
            field=models.CharField(db_index=True, max_length=50),
        ),
    ]

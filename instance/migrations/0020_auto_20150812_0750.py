# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0019_auto_20150808_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='base_domain',
            field=models.CharField(default='plebia.net', max_length=50),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_admin_organization_name',
            field=models.CharField(default='', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_organization_name',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_repository_name',
            field=models.CharField(db_index=True, max_length=200),
        ),
    ]

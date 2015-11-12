# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0035_reset_ansible_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='ansible_source_repo_url',
            field=models.URLField(blank=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='configuration_version',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]

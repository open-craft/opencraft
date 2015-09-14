# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0023_openedxinstance_ansible_source_repo_url'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='instancelogentry',
            options={'verbose_name_plural': 'Instance Log Entries'},
        ),
        migrations.AlterModelOptions(
            name='serverlogentry',
            options={'verbose_name_plural': 'Server Log Entries'},
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='github_pr_number',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='base_domain',
            field=models.CharField(max_length=50, default='example.com'),
        ),
    ]

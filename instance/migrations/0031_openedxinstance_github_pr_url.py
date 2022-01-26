# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


def migrate_urls(apps, schema_editor):
    Instance = apps.get_model("instance", "OpenEdXInstance")
    instances = Instance.objects.exclude(github_pr_number__isnull=True)
    for instance in instances:
        instance.github_pr_url = 'https://github.com/{fork}/pull/{number}'.format(
            fork=getattr(settings, 'DEFAULT_FORK', 'openedx/edx-platform'),
            number=instance.github_pr_number
        )
        instance.save()


def reverse_migrate_urls(apps, schema_editor):
    Instance = apps.get_model("instance", "OpenEdXInstance")
    instances = Instance.objects.exclude(github_pr_url='')
    for instance in instances:
        instance.github_pr_number = int(instance.github_pr_url.split('/')[-1])
        instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0030_auto_20150927_1045'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='github_pr_url',
            field=models.URLField(blank=True),
        ),
        migrations.RunPython(migrate_urls, reverse_code=reverse_migrate_urls),
        migrations.RemoveField(
            model_name='openedxinstance',
            name='github_pr_number',
        ),
    ]

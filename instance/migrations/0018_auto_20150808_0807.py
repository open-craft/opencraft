# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0017_openedxinstance_github_admin_organization_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_admin_organization_name',
            field=models.CharField(max_length=50, blank=True, default=''),
        ),
    ]

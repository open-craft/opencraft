# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0021_auto_20150816_0811'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='openedxinstance',
            options={'verbose_name': 'Open edX Instance', 'ordering': ['-created']},
        ),
    ]

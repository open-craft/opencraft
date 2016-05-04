# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('instance', '0046_generic_logging2'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GeneralLogEntry',
        ),
        migrations.RemoveField(
            model_name='instancelogentry',
            name='obj',
        ),
        migrations.RemoveField(
            model_name='serverlogentry',
            name='obj',
        ),
        migrations.DeleteModel(
            name='InstanceLogEntry',
        ),
        migrations.DeleteModel(
            name='ServerLogEntry',
        ),
    ]

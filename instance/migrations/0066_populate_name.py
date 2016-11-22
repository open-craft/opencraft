# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_name(apps, schema_editor):
    dbs = (
        apps.get_model('instance', model)
        for model in ['MySQLServer', 'MongoDBServer']
    )
    for model in dbs:
        for row in model.objects.all():
            row.name = row.hostname
            row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0065_create_description'),
    ]

    operations = [
        migrations.RunPython(
            populate_name,
            reverse_code=migrations.RunPython.noop
        ),
    ]

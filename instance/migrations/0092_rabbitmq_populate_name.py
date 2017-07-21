# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_name(apps, schema_editor):
    model = apps.get_model('instance', 'RabbitMQServer')
    for row in model.objects.all():
        row.name = row.instance_host
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0091_support_multiple_rabbitmq_servers'),
    ]

    operations = [
        migrations.RunPython(
            populate_name,
            reverse_code=migrations.RunPython.noop
        ),
    ]

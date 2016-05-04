# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import instance.models.instance
import instance.models.mixins.utilities
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0049_appserver_refactor2'),
    ]

    operations = [
        # TODO: Uncomment this once deemed safe
        migrations.AlterField(model_name='openstackserver', name='instance', field=models.IntegerField(db_column='instance_id', null=True)),
        #migrations.RemoveField(model_name='openstackserver', name='instance'),
        #migrations.DeleteModel(name='SingleVMOpenEdXInstance'),
    ]

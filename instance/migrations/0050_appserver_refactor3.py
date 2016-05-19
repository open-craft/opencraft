# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0049_appserver_refactor2'),
    ]

    operations = [
        migrations.RemoveField(model_name='openstackserver', name='instance'),
        migrations.DeleteModel(name='SingleVMOpenEdXInstance'),
    ]

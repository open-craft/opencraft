# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0040_auto_20160416_1735'),
    ]

    operations = [
        migrations.RenameModel('OpenEdXInstance', 'SingleVMOpenEdXInstance'),
        migrations.AlterField(
            model_name='instancelogentry',
            name='obj',
            field=models.ForeignKey(related_name='log_entry_set', to='instance.SingleVMOpenEdXInstance', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='instance',
            field=models.ForeignKey(related_name='server_set', to='instance.SingleVMOpenEdXInstance', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]

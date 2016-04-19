# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0038_merge'),
    ]

    operations = [
        migrations.RenameModel('OpenEdXInstance', 'SingleVMOpenEdXInstance'),
        migrations.AlterField(
            model_name='instancelogentry',
            name='obj',
            field=models.ForeignKey(related_name='log_entry_set', to='instance.SingleVMOpenEdXInstance'),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='instance',
            field=models.ForeignKey(related_name='server_set', to='instance.SingleVMOpenEdXInstance'),
        ),
    ]

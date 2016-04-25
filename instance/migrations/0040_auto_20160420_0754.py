# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from instance.models.instance import Status as InstanceStatus


def set_instance_states(apps, schema_editor):
    SingleVMOpenEdXInstance = apps.get_model("instance", "SingleVMOpenEdXInstance")
    SingleVMOpenEdXInstance.objects.filter(
        server_set__status__in=("new", "started", "active", "rebooting")).update(
            _status=InstanceStatus.WaitingForServer.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set__status__in=("booted", "ready")).update(
            _status=InstanceStatus.Running.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set__status="provisioning").update(
            _status=InstanceStatus.ConfiguringServer.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set__status="terminated").update(
            _status=InstanceStatus.Terminated.state_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0039_auto_20160419_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlevmopenedxinstance',
            name='_status',
            field=models.CharField(choices=[('terminated', 'Terminated'), ('configuring', 'ConfiguringServer'), ('failed', 'ConfigurationFailed'), ('waiting', 'WaitingForServer'), ('new', 'New'), ('running', 'Running'), ('error', 'Error')], db_column='status', default='new', max_length=20, db_index=True)
        ),
        migrations.RunPython(set_instance_states, migrations.RunPython.noop),
    ]

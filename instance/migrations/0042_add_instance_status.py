# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from instance.models.instance import Status as InstanceStatus


def set_instance_states(apps, schema_editor):
    SingleVMOpenEdXInstance = apps.get_model("instance", "SingleVMOpenEdXInstance")
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status__in=("new", "active")).update(
            _status=InstanceStatus.WaitingForServer.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status="started", server_set___progress__in=("running", "success")).update(
            _status=InstanceStatus.WaitingForServer.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status="started", server_set___progress="failed").update(
            _status=InstanceStatus.Error.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status__in=("booted", "ready")).update(
            _status=InstanceStatus.Running.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status="provisioning", server_set___progress__in=("running", "success")).update(
            _status=InstanceStatus.ConfiguringServer.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status="provisioning", server_set___progress="failed").update(
            _status=InstanceStatus.ConfigurationFailed.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status="rebooting").update(
            _status=InstanceStatus.ConfiguringServer.state_id
        )
    SingleVMOpenEdXInstance.objects.filter(
        server_set___status="terminated").update(
            _status=InstanceStatus.Terminated.state_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0041_rename_openedxinstance'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlevmopenedxinstance',
            name='_status',
            field=models.CharField(choices=[('configuring', 'ConfiguringServer'), ('error', 'Error'), ('failed', 'ConfigurationFailed'), ('new', 'New'), ('running', 'Running'), ('terminated', 'Terminated'), ('waiting', 'WaitingForServer')], db_column='status', default='new', max_length=20, db_index=True),
        ),
        migrations.RunPython(set_instance_states, migrations.RunPython.noop),
    ]

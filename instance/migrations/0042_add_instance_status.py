# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

class InstanceStatus:
    """ Frozen copy of InstanceStatus constants at this point in the migration history """
    class New:
        state_id = 'new'
    class WaitingForServer:
        state_id = 'waiting'
    class ConfiguringServer:
        state_id = 'configuring'
    class Running:
        state_id = 'running'
    class ConfigurationFailed:
        state_id = 'failed'
    class Error:
        state_id = 'error'
    class Terminated:
        state_id = 'terminated'


def get_current_server(instance):
    return instance.server_set.order_by("id").last()

def get_instance_state(server_status, server_progress):
    if server_status in ("new", "active"):
        return InstanceStatus.WaitingForServer.state_id
    if server_status == "started":
        if server_progress in ("running", "success"):
            return InstanceStatus.WaitingForServer.state_id
        elif server_progress == "failed":
            return InstanceStatus.Error.state_id
    if server_status in ("booted", "ready"):
        return InstanceStatus.Running.state_id
    if server_status == "provisioning":
        if server_progress in ("running", "success"):
            return InstanceStatus.ConfiguringServer.state_id
        elif server_progress == "failed":
            return InstanceStatus.ConfigurationFailed.state_id
    if server_status == "rebooting":
        return InstanceStatus.ConfiguringServer.state_id
    if server_status == "terminated":
        return InstanceStatus.Terminated.state_id

def set_instance_states(apps, schema_editor):
    SingleVMOpenEdXInstance = apps.get_model("instance", "SingleVMOpenEdXInstance")
    for instance in SingleVMOpenEdXInstance.objects.iterator():
        current_server = get_current_server(instance)
        if current_server:  # instance.server_set contains at least one server
            server_status = current_server._status
            server_progress = current_server._progress
            instance._status = get_instance_state(server_status, server_progress)
        else:  # instance.server_set is empty (this happens when there are more instances created than workers are available to spawn servers)
            instance._status = InstanceStatus.New.state_id
        instance.save()


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

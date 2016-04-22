# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_instance_states(apps, schema_editor):
    SingleVMOpenEdXInstance = apps.get_model("instance", "SingleVMOpenEdXInstance")
    for instance in SingleVMOpenEdXInstance.objects.iterator():
        server_status = instance.server_status
        if server_status:
            if server_status.state_id in ("new", "started", "active", "rebooting"):
                instance._status_to_waiting_for_server()
            elif server_status.state_id in ("booted", "ready"):
                instance._status_to_waiting_for_server()
                instance._status_to_configuring_server()
                instance._status_to_running()
            elif server_status.state_id == "provisioning":
                instance._status_to_waiting_for_server()
                instance._status_to_configuring_server()
            elif server_status.state_id == "terminated":
                instance._status_to_waiting_for_server()
                instance._status_to_configuring_server()
                instance._status_to_running()
                instance._status_to_terminated()


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0039_auto_20160419_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlevmopenedxinstance',
            name='status',
            field=models.CharField(choices=[('terminated', 'Terminated'), ('configuring', 'ConfiguringServer'), ('failed', 'ConfigurationFailed'), ('waiting', 'WaitingForServer'), ('new', 'New'), ('running', 'Running'), ('error', 'Error')], default='new', max_length=20, db_index=True)
        ),
        migrations.RunPython(set_instance_states, migrations.RunPython.noop),
    ]

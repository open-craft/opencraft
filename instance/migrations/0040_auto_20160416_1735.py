# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0039_auto_20160416_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='openedxinstance',
            name='swift_openstack_auth_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='swift_openstack_password',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='swift_openstack_region',
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='swift_openstack_tenant',
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='swift_openstack_user',
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='swift_provisioned',
            field=models.BooleanField(default=False),
        ),
    ]

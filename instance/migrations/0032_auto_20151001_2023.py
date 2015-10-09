# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields
import django.db.models.fields
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0031_openedxinstance_github_pr_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='DigitalOceanServer',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, default=django.db.models.fields.NOT_PROVIDED, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, default=django.db.models.fields.NOT_PROVIDED, verbose_name='modified')),
                ('status', models.CharField(db_index=True, choices=[('new', 'New - Not yet loaded'), ('started', 'Started - Running but not active yet'), ('active', 'Active - Running but not booted yet'), ('booted', 'Booted - Booted but not ready to be added to the application'), ('provisioned', 'Provisioned - Provisioning is completed'), ('rebooting', 'Rebooting - Reboot in progress, to apply changes from provisioning'), ('ready', 'Ready - Rebooted and ready to add to the application'), ('live', 'Live - Is actively used in the application and/or accessed by users'), ('stopping', 'Stopping - Stopping temporarily'), ('stopped', 'Stopped - Stopped temporarily'), ('terminating', 'Terminating - Stopping forever'), ('terminated', 'Terminated - Stopped forever')], default='new', max_length=11)),
                ('droplet_id', models.CharField(db_index=True, blank=True, max_length=250)),
                ('instance', models.ForeignKey(to='instance.OpenEdXInstance')),
            ],
            options={
                'abstract': False,
            },
            bases=(instance.models.utils.ValidateModelMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='instance',
            field=models.ForeignKey(to='instance.OpenEdXInstance'),
        ),
    ]

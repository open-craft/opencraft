# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OpenEdXInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(editable=False, blank=True, default=django.utils.timezone.now, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(editable=False, blank=True, default=django.utils.timezone.now, verbose_name='modified')),
                ('sub_domain', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('name', models.CharField(max_length=50)),
                ('base_domain', models.CharField(max_length=50, default='openedxhosting.com')),
                ('protocol', models.CharField(max_length=5, choices=[('http', 'HTTP - Unencrypted clear text'), ('https', 'HTTPS - Encrypted')], default='http')),
                ('branch_name', models.CharField(max_length=50, default='master')),
                ('commit_id', models.CharField(max_length=40, default='master')),
                ('github_organization_name', models.CharField(max_length=50, db_index=True)),
                ('github_repository_name', models.CharField(max_length=50, db_index=True)),
                ('ansible_playbook', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenStackServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(editable=False, blank=True, default=django.utils.timezone.now, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(editable=False, blank=True, default=django.utils.timezone.now, verbose_name='modified')),
                ('status', models.CharField(max_length=10, choices=[('new', 'New - Not yet loaded'), ('started', 'Started - Running but not active yet'), ('active', 'Active - Running but not booted yet'), ('booted', 'Booted - Booted but not ready to be added to the application'), ('ready', 'Ready - Ready to be added to the application'), ('live', 'Live - Is actively used in the application and/or accessed by users'), ('stopping', 'Stopping - Stopping temporarily'), ('stopped', 'Stopped - Stopped temporarily'), ('terminating', 'Terminating - Stopping forever'), ('terminated', 'Terminated - Stopped forever')], default='new', db_index=True)),
                ('openstack_id', models.CharField(max_length=250, db_index=True)),
                ('instance', models.ForeignKey(related_name='server_set', to='instance.OpenEdXInstance')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

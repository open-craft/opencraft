# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0002_auto_20150530_1255'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstanceLogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', default=django.utils.timezone.now, editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', default=django.utils.timezone.now, editable=False, blank=True)),
                ('text', models.TextField()),
                ('level', models.CharField(max_length=5, db_index=True, default='info', choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('exception', 'Exception')])),
                ('instance', models.ForeignKey(related_name='logentry_set', to='instance.OpenEdXInstance')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServerLogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', default=django.utils.timezone.now, editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', default=django.utils.timezone.now, editable=False, blank=True)),
                ('text', models.TextField()),
                ('level', models.CharField(max_length=5, db_index=True, default='info', choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('exception', 'Exception')])),
                ('server', models.ForeignKey(related_name='logentry_set', to='instance.OpenStackServer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='logentry',
            name='instance',
        ),
        migrations.DeleteModel(
            name='LogEntry',
        ),
    ]

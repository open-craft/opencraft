# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('instance', '0044_remove_server_progress'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(verbose_name='created', auto_now_add=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(verbose_name='modified', auto_now=True)),
                ('text', models.TextField(blank=True)),
                ('level', models.CharField(db_index=True, choices=[('DEBUG', 'Debug'), ('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error'), ('CRITICAL', 'Critical')], default='INFO', max_length=9)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='+', null=True, blank=True, on_delete=django.db.models.deletion.CASCADE)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ('-created',),
                'verbose_name_plural': 'Log Entries',
                'permissions': (('read_log_entry', 'Can read LogEntry'),),
            },
            bases=(instance.models.utils.ValidateModelMixin, models.Model),
        ),
    ]

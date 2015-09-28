# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import instance.models.utils
import django.db.models.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0024_auto_20150911_2304'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralLogEntry',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='created', auto_now_add=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, default=django.db.models.fields.NOT_PROVIDED, verbose_name='modified')),
                ('text', models.TextField(blank=True)),
                ('level', models.CharField(db_index=True, default='info', max_length=9, choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error'), ('exception', 'Exception')])),
            ],
            options={
                'verbose_name_plural': 'General Log Entries',
            },
            bases=(instance.models.utils.ValidateModelMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='base_domain',
            field=models.CharField(default='plebia.net', max_length=50),
        ),
    ]

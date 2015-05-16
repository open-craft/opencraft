# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(blank=True, verbose_name='description', null=True)),
                ('slug', django_extensions.db.fields.AutoSlugField(verbose_name='slug', editable=False, blank=True, populate_from='title')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
    ]

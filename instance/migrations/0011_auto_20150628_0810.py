# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields
import django.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0010_openedxinstance_ref_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instancelogentry',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='instancelogentry',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='openstackserver',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='created',
            field=django_extensions.db.fields.CreationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='created', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='serverlogentry',
            name='modified',
            field=django_extensions.db.fields.ModificationDateTimeField(default=django.db.models.fields.NOT_PROVIDED, verbose_name='modified', auto_now=True),
        ),
    ]

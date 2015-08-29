# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('text', models.TextField()),
                ('level', models.CharField(max_length=5, default='info', choices=[('debug', 'Debug'), ('info', 'Info'), ('warn', 'Warning'), ('error', 'Error')], db_index=True)),
            ],
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='email',
            field=models.EmailField(max_length=254, default='contact@example.com'),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_organization_name',
            field=models.CharField(max_length=50, default='open-craft', db_index=True),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='github_repository_name',
            field=models.CharField(max_length=50, default='opencraft', db_index=True),
        ),
        migrations.AddField(
            model_name='logentry',
            name='instance',
            field=models.ForeignKey(to='instance.OpenEdXInstance'),
        ),
    ]

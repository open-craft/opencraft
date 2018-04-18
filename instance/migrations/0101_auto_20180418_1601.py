# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-04-18 22:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import instance.models.mixins.database


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0100_decline_new_clients_backends_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='MongoDBReplicaSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(blank=True, max_length=250)),
            ],
            options={
                'verbose_name': 'MongoDB Replica Set',
            },
        ),
        migrations.AddField(
            model_name='mongodbserver',
            name='replica_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='instance.MongoDBReplicaSet'),
        ),
        migrations.AddField(
            model_name='mongodbserver',
            name='primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='mongodb_replica_set',
            field=models.ForeignKey(blank=True, default=instance.models.mixins.database.select_random_mongodb_replica_set, null=True, on_delete=django.db.models.deletion.PROTECT, to='instance.MongoDBReplicaSet'),
        ),
        migrations.AlterField(
            model_name='openedxinstance',
            name='mongodb_server',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='instance.MongoDBServer'),
        ),
    ]

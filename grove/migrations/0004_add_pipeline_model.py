# Generated by Django 2.2.24 on 2022-02-18 08:16

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0144_make_redis_username_unique'),
        ('grove', '0003_additional_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='GitlabPipeline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('status', models.SmallIntegerField(choices=[(0, 'Created'), (1, 'Running'), (2, 'Success'), (3, 'Failed'), (4, 'Skipped'), (5, 'Cancelled')], default=0)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='instance.InstanceReference')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='grovedeployment',
            name='pipeline',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='grove.GitlabPipeline'),
        ),
    ]

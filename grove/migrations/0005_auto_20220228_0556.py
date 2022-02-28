# Generated by Django 2.2.24 on 2022-02-28 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grove', '0004_auto_20220218_0816'),
    ]

    operations = [
        migrations.AddField(
            model_name='gitlabpipeline',
            name='pipeline_id',
            field=models.PositiveIntegerField(blank=True, help_text='Gitlab Pipeline ID', null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='gitlabpipeline',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'created'), (1, 'running'), (2, 'success'), (3, 'failed'), (4, 'skipped'), (5, 'cancelled')], default=0),
        ),
        migrations.AlterField(
            model_name='grovedeployment',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'Triggered Deployment'), (2, 'Deployed'), (3, 'Cancelled')], default=0),
        ),
    ]

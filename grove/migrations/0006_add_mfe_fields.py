# Generated by Django 2.2.24 on 2022-03-09 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grove', '0005_update_status_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='groveinstance',
            name='external_mfe_domain',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='groveinstance',
            name='internal_mfe_domain',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
    ]

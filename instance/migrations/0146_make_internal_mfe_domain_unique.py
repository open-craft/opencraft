# Generated by Django 2.2.24 on 2021-12-13 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0145_add_mfe_domain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openedxinstance',
            name='internal_mfe_domain',
            field=models.CharField(max_length=100, unique=True),
        )
    ]

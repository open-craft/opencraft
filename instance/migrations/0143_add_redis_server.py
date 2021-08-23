# Generated by Django 2.2.24 on 2021-08-13 08:53

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import instance.models.mixins.redis
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0142_add_cache_db_to_openedxinstance'),
    ]

    operations = [
        migrations.CreateModel(
            name='RedisServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(max_length=250)),
                ('description', models.CharField(blank=True, max_length=250)),
                ('admin_username', models.CharField(max_length=64)),
                ('admin_password', models.CharField(max_length=128)),
                ('instance_host', models.CharField(max_length=128)),
                ('instance_port', models.PositiveIntegerField(default=5671)),
                ('instance_db', models.PositiveIntegerField(default=0)),
                ('use_ssl_connections', models.BooleanField(default=True)),
                ('accepts_new_clients', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Redis Server',
            },
            bases=(instance.models.utils.ValidateModelMixin, models.Model),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='redis_password',
            field=models.CharField(default=instance.models.mixins.redis.random_password, max_length=64),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='redis_provisioned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='redis_username',
            field=models.CharField(default=instance.models.mixins.redis.random_username, max_length=32, unique=True),
        ),
        migrations.AddField(
            model_name='openedxinstance',
            name='redis_server',
            field=models.ForeignKey(blank=True, default=instance.models.mixins.redis.select_random_redis_server, null=True, on_delete=django.db.models.deletion.PROTECT, to='instance.RedisServer'),
        ),
    ]
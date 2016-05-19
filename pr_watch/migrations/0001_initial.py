# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('instance', '0048_appserver_refactor1'),
    ]

    operations = [
        migrations.CreateModel(
            name='WatchedPullRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch_name', models.CharField(default='master', max_length=50)),
                ('ref_type', models.CharField(default='heads', max_length=50)),
                ('github_organization_name', models.CharField(db_index=True, max_length=200)),
                ('github_repository_name', models.CharField(db_index=True, max_length=200)),
                ('github_pr_url', models.URLField(blank=False)),
                ('instance', models.OneToOneField(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to='instance.OpenEdXInstance')),
            ],
        ),
    ]

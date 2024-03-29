# Generated by Django 2.2.24 on 2022-01-16 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grove', '0002_add_storage_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='groveclusterrepository',
            name='personal_access_token',
            field=models.CharField(blank=True, default=None, help_text='GitLab Personal Access Token', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='groveclusterrepository',
            name='username',
            field=models.CharField(blank=True, default=None, help_text='GitLab username', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='grovedeployment',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'Triggered Deployment'), (2, 'Deployed')], default=0),
        ),
        migrations.AddField(
            model_name='groveinstance',
            name='successfully_provisioned',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='groveclusterrepository',
            name='git_ref',
            field=models.CharField(default='main', help_text='Git branch or tag on the repository to use when triggering pipelines.', max_length=255),
        ),
        migrations.AlterField(
            model_name='groveclusterrepository',
            name='trigger_token',
            field=models.CharField(blank=True, default=None, help_text='GitLab token used to trigger pipeline builds.', max_length=255, null=True),
        ),
    ]

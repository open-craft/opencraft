# Generated by Django 2.2.24 on 2022-04-30 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grove', '0007_groveclusterrepository_git_repo_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groveclusterrepository',
            name='personal_access_token',
            field=models.CharField(default=' ', help_text='GitLab Personal Access Token', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groveclusterrepository',
            name='trigger_token',
            field=models.CharField(default=' ', help_text='GitLab token used to trigger pipeline builds.', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groveclusterrepository',
            name='username',
            field=models.CharField(default=' ', help_text='GitLab username', max_length=255),
            preserve_default=False,
        ),
    ]

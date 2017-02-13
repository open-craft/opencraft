# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import instance.models.mixins.utilities
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('instance', '0047_generic_logging3'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstanceReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('name', models.CharField(default='Instance', max_length=250)),
                ('instance_id', models.PositiveIntegerField()),
                ('instance_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.RunSQL(
            # Since InstanceReference can support multiple types of instance, it is important that
            # the code never assumes that OpenEdXInstance.id == InstanceReference.id. To help
            # enforce that, we use this custom SQL to ensure that InstanceReference IDs are
            # multiples of 10, while Instance/OpenEdXInstance IDs will behave normally:
            ["ALTER SEQUENCE instance_instancereference_id_seq INCREMENT BY 10 RESTART WITH 10;"]
        ),
        migrations.CreateModel(
            name='OpenEdXAppServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('_status', models.CharField(choices=[('configuring', 'ConfiguringServer'), ('error', 'Error'), ('failed', 'ConfigurationFailed'), ('new', 'New'), ('running', 'Running'), ('terminated', 'Terminated'), ('waiting', 'WaitingForServer')], db_column='status', db_index=True, default='new', max_length=20)),
                ('name', models.CharField(max_length=250)),
                ('email', models.EmailField(default='contact@example.com', help_text='The default contact email for this instance; also used as the from address for emails sent by the server.', max_length=254)),
                ('protocol', models.CharField(choices=[('http', 'HTTP - Unencrypted clear text'), ('https', 'HTTPS - Encrypted')], default='http', max_length=5)),
                ('configuration_source_repo_url', models.URLField(max_length=256)),
                ('configuration_version', models.CharField(max_length=50)),
                ('configuration_extra_settings', models.TextField(blank=True, help_text='YAML config vars that override all others')),
                ('edx_platform_repository_url', models.CharField(help_text='URL to the edx-platform repository to use. Leave blank for default.', max_length=256)),
                ('edx_platform_commit', models.CharField(help_text='edx-platform commit hash or branch or tag to use. Leave blank to use the default, which is equal to the value of "openedx_release".', max_length=256)),
                ('openedx_release', models.CharField(help_text='Set this to a release tag like "named-release/dogwood" to build a specific release of Open edX. This setting becomes the default value for edx_platform_version, forum_version, notifier_version, xqueue_version, and certs_version so it should be a git branch that exists in all of those repositories. Note: to build a specific branch of edx-platform, you should just override edx_platform_commit rather than changing this setting. Note 2: This value does not affect the default value of configuration_version.', max_length=128)),
                ('use_ephemeral_databases', models.BooleanField()),
                ('github_admin_organization_name', models.CharField(blank=True, default='', help_text="GitHub organization whose users will be given SSH access to this instance's VMs", max_length=200)),
                ('configuration_database_settings', models.TextField(blank=True, help_text='YAML vars for database configuration')),
                ('configuration_storage_settings', models.TextField(blank=True, help_text='YAML vars for storage configuration')),
                ('configuration_settings', models.TextField(help_text='A record of the combined (final) ansible variables passed to the configuration playbook when configuring this AppServer.')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='openedxappserver_set', to='instance.InstanceReference')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Open edX App Server',
            },
            bases=(instance.models.utils.ValidateModelMixin, models.Model, instance.models.mixins.utilities.EmailMixin),
        ),
        migrations.CreateModel(
            name='OpenEdXInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mysql_user', models.CharField(blank=True, max_length=16)),
                ('mysql_pass', models.CharField(blank=True, max_length=32)),
                ('mysql_provisioned', models.BooleanField(default=False)),
                ('mongo_user', models.CharField(blank=True, max_length=16)),
                ('mongo_pass', models.CharField(blank=True, max_length=32)),
                ('mongo_provisioned', models.BooleanField(default=False)),
                ('swift_openstack_user', models.CharField(blank=True, max_length=32)),
                ('swift_openstack_password', models.CharField(blank=True, max_length=64)),
                ('swift_openstack_tenant', models.CharField(blank=True, max_length=32)),
                ('swift_openstack_auth_url', models.URLField(blank=True)),
                ('swift_openstack_region', models.CharField(blank=True, max_length=16)),
                ('swift_provisioned', models.BooleanField(default=False)),
                ('email', models.EmailField(default='contact@example.com', help_text='The default contact email for this instance; also used as the from address for emails sent by the server.', max_length=254)),
                ('protocol', models.CharField(choices=[('http', 'HTTP - Unencrypted clear text'), ('https', 'HTTPS - Encrypted')], default='http', max_length=5)),
                ('configuration_source_repo_url', models.URLField(max_length=256)),
                ('configuration_version', models.CharField(max_length=50)),
                ('configuration_extra_settings', models.TextField(blank=True, help_text='YAML config vars that override all others')),
                ('edx_platform_repository_url', models.CharField(help_text='URL to the edx-platform repository to use. Leave blank for default.', max_length=256)),
                ('edx_platform_commit', models.CharField(help_text='edx-platform commit hash or branch or tag to use. Leave blank to use the default, which is equal to the value of "openedx_release".', max_length=256)),
                ('openedx_release', models.CharField(help_text='Set this to a release tag like "named-release/dogwood" to build a specific release of Open edX. This setting becomes the default value for edx_platform_version, forum_version, notifier_version, xqueue_version, and certs_version so it should be a git branch that exists in all of those repositories. Note: to build a specific branch of edx-platform, you should just override edx_platform_commit rather than changing this setting. Note 2: This value does not affect the default value of configuration_version.', max_length=128)),
                ('s3_access_key', models.CharField(blank=True, max_length=50)),
                ('s3_secret_access_key', models.CharField(blank=True, max_length=50)),
                ('s3_bucket_name', models.CharField(blank=True, max_length=50)),
                ('use_ephemeral_databases', models.BooleanField()),
                ('github_admin_organization_name', models.CharField(blank=True, default='', help_text="GitHub organization whose users will be given SSH access to this instance's VMs", max_length=200)),
                ('sub_domain', models.CharField(max_length=50)),
                ('base_domain', models.CharField(blank=True, max_length=50)),
                ('active_appserver', models.OneToOneField(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='instance.OpenEdXAppServer')),
            ],
            options={
                'verbose_name': 'Open edX Instance',
            },
        ),
        migrations.AlterModelOptions(
            name='openstackserver',
            options={'verbose_name': 'OpenStack VM'},
        ),
        migrations.AddField(
            model_name='openstackserver',
            name='name_prefix',
            field=models.SlugField(default='edxapp-old', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='openedxappserver',
            name='server',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='instance.OpenStackServer'),
        ),
        migrations.AlterUniqueTogether(
            name='openedxinstance',
            unique_together=set([('base_domain', 'sub_domain')]),
        ),
        migrations.AlterUniqueTogether(
            name='instancereference',
            unique_together=set([('instance_type', 'instance_id')]),
        ),
    ]

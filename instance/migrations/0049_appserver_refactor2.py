# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('instance', '0048_appserver_refactor1'),
        ('pr_watch', '0001_initial'),
    ]

    def data_forward(apps, schema_editor):
        """
        Move existing data from SingleVMOpenEdXInstance to OpenEdXInstance + OpenEdXAppServer
        """
        # Unchanged models:
        ContentType = apps.get_model('contenttypes', 'ContentType')
        OpenStackServer = apps.get_model('instance', 'OpenStackServer')
        # Old models:
        SingleVMOpenEdXInstance = apps.get_model('instance', 'SingleVMOpenEdXInstance')
        # New models:
        OpenEdXInstance = apps.get_model('instance', 'OpenEdXInstance')
        OpenEdXAppServer = apps.get_model('instance', 'OpenEdXAppServer')
        WatchedPullRequest = apps.get_model('pr_watch', 'WatchedPullRequest')
        
        for old_instance in SingleVMOpenEdXInstance.objects.all().order_by('pk'):
            # Compute the 'repository_url' property of old_instance since we need it but it's not directly available:
            repository_url = 'https://github.com/{}/{}.git'.format(
                old_instance.github_organization_name, old_instance.github_repository_name,
            )

            # Create the new OpenEdXInstance:
            new_instance = OpenEdXInstance.objects.create(
                # Main:
                name=old_instance.name,
                email=old_instance.email,
                protocol=old_instance.protocol,
                use_ephemeral_databases=old_instance.use_ephemeral_databases,
                github_admin_organization_name=old_instance.github_admin_organization_name,
                sub_domain=old_instance.sub_domain,
                base_domain=old_instance.base_domain,
                active_appserver=None,
                # Database:
                mysql_user=old_instance.mysql_user,
                mysql_pass=old_instance.mysql_pass,
                mysql_provisioned=old_instance.mysql_provisioned,
                mongo_user=old_instance.mongo_user,
                mongo_pass=old_instance.mongo_pass,
                mongo_provisioned=old_instance.mongo_provisioned,
                # Storage:
                swift_openstack_user=old_instance.swift_openstack_user,
                swift_openstack_password=old_instance.swift_openstack_password,
                swift_openstack_tenant=old_instance.swift_openstack_tenant,
                swift_openstack_auth_url=old_instance.swift_openstack_auth_url,
                swift_openstack_region=old_instance.swift_openstack_region,
                swift_provisioned=old_instance.swift_provisioned,
                s3_access_key=old_instance.s3_access_key,
                s3_secret_access_key=old_instance.s3_secret_access_key,
                s3_bucket_name=old_instance.s3_bucket_name,
                # Ansible:
                configuration_source_repo_url=old_instance.ansible_source_repo_url,
                configuration_version=old_instance.configuration_version,
                configuration_extra_settings=old_instance.ansible_extra_settings,
                edx_platform_repository_url=repository_url,
                edx_platform_commit=old_instance.commit_id,
                # openedx_release has replaced forum_version, notifier_version, etc. which were usually the same:
                openedx_release=old_instance.forum_version,
            )

            # Create the PR record, if any:
            if old_instance.github_pr_url:
                watched_pr = WatchedPullRequest.objects.create(
                    branch_name=old_instance.branch_name,
                    ref_type=old_instance.ref_type,
                    github_organization_name=old_instance.github_organization_name,
                    github_repository_name=old_instance.github_repository_name,
                    github_pr_url=old_instance.github_pr_url,
                    instance=new_instance,
                )

            # Get the VM, if any:
            current_vm = old_instance.server_set.order_by("id").last()
            if current_vm:
                # Create one AppServer:
                new_appserver = OpenEdXAppServer.objects.create(
                    # Relations to other objects:
                    owner_id=new_instance.ref.pk,
                    server=current_vm,
                    # Timestamps:
                    created=old_instance.created,
                    modified=old_instance.modified,
                    # Basic properties:
                    name="AppServer 1",
                    _status=old_instance._status,
                    # Main ansible var settings:
                    email=old_instance.email,
                    protocol=old_instance.protocol,
                    configuration_source_repo_url=old_instance.ansible_source_repo_url,
                    configuration_version=old_instance.configuration_version,
                    configuration_extra_settings=old_instance.ansible_extra_settings,
                    edx_platform_repository_url=repository_url,
                    edx_platform_commit=old_instance.commit_id,
                    openedx_release=new_instance.openedx_release,
                    use_ephemeral_databases=old_instance.use_ephemeral_databases,
                    github_admin_organization_name=old_instance.github_admin_organization_name,
                    # Derived ansible var YAML:
                    configuration_database_settings="",
                    configuration_storage_settings="",
                    configuration_settings=old_instance.ansible_settings,
                )
                if old_instance._status == 'running':
                    new_instance.active_appserver = new_appserver
                    new_instance.save()

            # Migrate LogEntry entries:
            LogEntry = apps.get_model('instance', 'logentry')
            old_instance_type = ContentType.objects.get_for_model(SingleVMOpenEdXInstance)
            new_instance_type = ContentType.objects.get_for_model(OpenEdXInstance)
            LogEntry.objects.filter(content_type=old_instance_type).update(content_type=new_instance_type)

    def data_backward(apps, schema_editor):
        """
        Reverse the data migration
        """
        raise NotImplementedError

    operations = [
        migrations.RunPython(data_forward, data_backward),
    ]

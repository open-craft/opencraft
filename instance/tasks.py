# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Imports #####################################################################

from huey.djhuey import crontab, db_periodic_task, task

from django.conf import settings

from instance.github import get_watched_pr_list
from .models import OpenEdXInstance


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Tasks #######################################################################

@task()
def provision_sandbox_instance(fork_name=None, **instance_field_dict):
    logger.info('Creating instance object for %s fork_name=%s', instance_field_dict, fork_name)
    instance, _ = OpenEdXInstance.objects.get_or_create(**instance_field_dict)

    # Set fork
    if fork_name is None:
        fork_name = settings.DEFAULT_FORK
    instance.set_fork_name(fork_name, commit=False)
    instance.set_to_branch_tip()

    # Include commit hash in name
    instance.name = '{instance.name} Sandbox ({instance.fork_name}/{instance.commit_short_id})'\
                    .format(instance=instance)

    logger.info('Running provisioning on %s', instance)
    _, log = instance.run_provisioning()
    return log

@task()
def watch_pr():
    for pr in get_watched_pr_list():
        provision_sandbox_instance(
            sub_domain='pr{number}.sandbox'.format(number=pr.number),
            name=pr.name,
            fork_name=pr.fork_name,
            branch_name=pr.branch_name,
            extra_ansible_settings=pr.extra_settings,
        )
    return None

@db_periodic_task(crontab(day='*'))
def update_instance_on_new_commit():
    #for instance in Instance.objects.all():
    pass

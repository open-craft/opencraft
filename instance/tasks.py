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
    instance.set_fork_name(fork_name)

    # Include commit hash in name
    instance.name = '{instance.name} Sandbox ({instance.fork_name}/{instance.commit_short_id})'\
                    .format(instance=instance)

    logger.info('Running provisioning on %s', instance)
    _, log = instance.run_provisioning()
    return log

@task()
def watch_pr():
    pr_list = get_watched_pr_list()

    # TODO: Update all PRs
    pr=pr_list[0]
    return provision_sandbox_instance(
        sub_domain='pr.sandbox', # TODO: set to 'pr<number>'
        name=pr.name,
        fork_name=pr.fork_name,
        branch_name=pr.branch_name,
        commit_id=pr.branch_name, # TODO: check if it needs to be updated for existing instances
    )

@db_periodic_task(crontab(day='*'))
def update_instance_on_new_commit():
    #for instance in Instance.objects.all():
    pass

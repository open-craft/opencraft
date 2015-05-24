# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Imports #####################################################################

from huey.djhuey import crontab, db_periodic_task, task

from .models import OpenEdXInstance


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Tasks #######################################################################

@task()
def provision_sandbox_instance(sub_domain, instance_name):
    logger.info('Create local instance object')
    instance, _ = OpenEdXInstance.objects.get_or_create(
        sub_domain=sub_domain,
        name=instance_name,
        ansible_playbook='edx_sandbox',
    )

    logger.info('Running provisioning on %s', instance)
    _, log = instance.run_provisioning()
    return log

@db_periodic_task(crontab(day='*'))
def update_instance_on_new_commit():
    #for instance in Instance.objects.all():
    pass

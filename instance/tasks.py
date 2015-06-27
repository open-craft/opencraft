# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Worker tasks for instance hosting & management
"""

# Imports #####################################################################

from huey.djhuey import task

from django.conf import settings

from instance.github import get_watched_pr_list
from .models import OpenEdXInstance


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Tasks #######################################################################

@task()
def provision_sandbox_instance(fork_name=None, **instance_field_dict):
    """
    (Re-)create sandbox instance & run provisioning on it
    """
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
    """
    Automatically create or recreate sandboxes for each of the open PRs from the watched
    organization on the watched repository
    """
    for pr in get_watched_pr_list():
        provision_sandbox_instance(
            sub_domain='pr{number}.sandbox'.format(number=pr.number),
            name=pr.name,
            fork_name=pr.fork_name,
            branch_name=pr.branch_name,
            ansible_extra_settings=pr.extra_settings,
        )
    return None

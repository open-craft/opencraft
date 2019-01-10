# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2018 OpenCraft <xavier@opencraft.com>
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
Worker tasks for building servers from edx/edx-platform at fixed time intervals.
"""

# Imports #####################################################################

import logging

from huey.contrib.djhuey import crontab, db_periodic_task

from instance.models.database_server import MongoDBServer
from instance.models.mixins.domain_names import generate_internal_lms_domain
from instance.models.mixins.database import select_random_mongodb_server
from instance.models.openedx_instance import OpenEdXInstance
from instance.tasks import spawn_appserver


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################

@db_periodic_task(crontab(hour='*/4'))
def deploy_edx_edxplatform():
    """
    Automatically deploy a new server with the latest version of Open edX.
    It uses the master branch from https://github.com/edx/edx-platform, https://github.com/edx/configuration and
    downloads all dependencies specified in the requirements files.
    It acts as a "continuous integration" system that uses Ocim's servers, including OVH and OpenStack, instead of
    the other technologies used in edX's CI system.
    The built version doesn't depend on any PRs (see WatchedFork and pr_watch for that).
    Because a deployment can take up to 2 hours, don't run this task more often than that, or else you'll have appserver overflow.
    """


    instance, created = OpenEdXInstance.objects.get_or_create(
        internal_lms_domain=generate_internal_lms_domain('master'), # FIXME just pass subdomain='master' or similar
        # github_admin_organizations=['open-craft'], # FIXME remove if possible, or assign OpenCraft organization. In any case, check that Ocim superusers still have SSH access (should always happen after sandboxes)
        use_ephemeral_databases=False, # FIXME this set to False was causing a problem with SWIFT because the "openstack" role wasn't in edx_sandbox.yml; see discovery document. Probably fixed; check
        edx_platform_repository_url='https://github.com/edx/edx-platform',
        configuration_source_repo_url='https://github.com/edx/configuration',
        configuration_version='master',
        edx_platform_commit='master',
        openedx_release='master',
        deploy_simpletheme=True, # FIXME add extra configuration variables that actually change some color, or disable 
    )
    if created:
        # Name is set separately because it's stored in InstanceReference
        instance.name = 'Integration - Open edX master periodic build'
        instance.save()

    # There is a wrapper around spawn_appserver that will check the build result and will send e-mails,
    # see in send_emails_on_deployment_failure
    spawn_appserver(instance.ref.pk, mark_active_on_success=False)


# TODO (after deploying 'master' works): add a similar function to deploy other branches
# E.g. apart from 'master', deploy and test also 'open-release/hawthorn.1'
# "cf OC-3150 – also add a second VM run that checks the stable branches used for beta instances are still working. Be sure to include an additional test lms_user, to mimic the beta instance creation logic."

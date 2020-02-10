# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
PR Watch app - PR sandbox creation management command.
"""
from urllib.parse import urlparse

from django.core.management.base import BaseCommand

from instance.tasks import spawn_appserver
from pr_watch.github import get_pr_by_number
from pr_watch.models import WatchedPullRequest

RELEASE_BRANCH_MAP = {
    'ginkgo': {
        'configuration_version': 'open-release/ginkgo.master',
        'openedx_release': 'open-release/ginkgo.master',
    },
    'hawthorn': {
        'configuration_version': 'open-release/hawthorn.master',
        'openedx_release': 'open-release/hawthorn.master',
    },
    'ironwood': {
        'configuration_version': 'open-release/ironwood.master',
        'openedx_release': 'open-release/ironwood.master',
    },
    'juniper': {
        'configuration_version': 'open-release/juniper.master',
        'openedx_release': 'open-release/juniper.master',
    }
}


class Command(BaseCommand):
    """
    Management command to set up a sandbox for provided PR link.
    """
    help = 'Sets up a Sandbox for the specified PR'

    def add_arguments(self, parser):
        parser.add_argument('pr_url')

    def handle(self, *args, **options):
        pr_url = urlparse(options['pr_url'])
        target_fork, pr_number = pr_url.path[1:].split('/pull/')
        pr = get_pr_by_number(target_fork, pr_number)
        instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, None)
        instance.configuration_playbook_name = None
        for release_name, release_config in RELEASE_BRANCH_MAP.items():
            if release_name in pr.target_branch:
                for key, val in release_config.items():
                    setattr(instance, key, val)
        instance.save()
        if created:
            spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        else:
            self.stderr.write(self.style.ERROR(
                f"Failed to create watched pull request for {pr_url.geturl()}"
            ))

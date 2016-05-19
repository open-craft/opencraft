# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
PR Watcher app models
"""

# Imports #####################################################################

import logging

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction

from instance.models.openedx_instance import OpenEdXInstance
from pr_watch import github
from pr_watch.github import fork_name2tuple
from pr_watch.logger_adapter import WatchedPullRequestLoggerAdapter


# Logging #####################################################################

logger = logging.getLogger(__name__)

# Validators ##################################################################

sha1_validator = RegexValidator(regex='^[0-9a-f]{40}$', message='Full SHA1 hash required')


# Models ######################################################################

class WatchedPullRequestQuerySet(models.QuerySet):
    """
    Additional methods for WatchedPullRequest querysets
    Also used as the standard manager for the WatchedPullRequest model
    """
    def update_or_create_from_pr(self, pr):
        """
        Create or update an instance for the given pull request
        """
        watched_pr, created = self.get_or_create(
            target_fork_name=pr.repo_name,
            github_pr_number=pr.github_pr_number,
        )
        watched_pr.update_instance_from_pr()
        return watched_pr.instance, created

    def create(self, *args, **kwargs):
        """
        Augmented `create()` method:
        - Adds support for `target_fork_name` to allow to set both the github target org & repo
        """
        target_fork_name = kwargs.pop('target_fork_name', None)
        if target_fork_name:
            kwargs['target_org'], kwargs['target_repo'] = fork_name2tuple(target_fork_name)
        watched_pr = self.model(**kwargs)
        self._for_write = True
        watched_pr.save(force_insert=True, using=self.db)
        return watched_pr

    def get(self, *args, **kwargs):
        """
        Augmented `get()` method:
        - Adds support for `target_fork_name` to allow to query the github org & repo using a single argument
        """
        target_fork_name = kwargs.pop('target_fork_name', None)
        if target_fork_name is not None:
            kwargs['target_org'], kwargs['target_repo'] = fork_name2tuple(target_fork_name)

        return super().get(*args, **kwargs)


class WatchedPullRequest(models.Model):
    """
    Represents a single watched pull request; holds the ID of the Instance created for that PR,
    if any
    """
    target_org = models.CharField(max_length=200, blank=False, help_text=(
        "GitHub organization name for the target repo (into which this PR will be merged)"
    ))
    target_repo = models.CharField(max_length=200, blank=False, help_text=(
        "GitHub repository name for the target repo (into which this PR will be merged)"
    ))
    pr_number = models.IntegerField(blank=False)
    instance = models.OneToOneField('instance.OpenEdXInstance', null=True, blank=True, on_delete=models.SET_NULL)

    objects = WatchedPullRequestQuerySet.as_manager()

    class Meta:
        unique_together = ('target_org', 'target_repo', 'pr_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = WatchedPullRequestLoggerAdapter(logger, {'obj': self})

    @property
    def target_fork_name(self):
        """
        Target fork name (eg. 'edx/edx-platform')
        """
        return '{0.github_target_org}/{0.github_target_repo}'.format(self)

    @property
    def github_pr_url(self):
        """
        Get the PR URL.
        """
        return 'https://github.com/{0.target_fork_name}/pull/{0.github_pr_number}'

    @property
    def target_fork_name(self):
        """
        Get the full name of the target repo/fork (e.g. 'edx/edx-platform')
        """
        # Split up a URL like https://github.com/edx/edx-platform/pull/12345678
        org, repo, pull, dummy = self.github_pr_url.split('/')[-4:]
        assert pull == "pull"
        return "{}/{}".format(org, repo)

    @property
    def repository_url(self):
        """
        URL of the git repository (eg. 'https://github.com/open-craft/edx-platform.git')
        """
        return '{0.github_base_url}.git'.format(self)

    @property
    def updates_feed(self):
        """
        RSS/Atom feed of commits made on the repository/branch
        """
        return '{0.github_base_url}/commits/{0.branch_name}.atom'.format(self)

    def update_instance_from_pr(self):
        """
        Update/create the associated sandbox instance with settings from this pull request.

        This will not spawn a new AppServer.
        This method will automatically save this WatchedPullRequest's 'instance' field.
        """
        # Fetch the latest PR data:
        pr = github.get_pr_by_number(self.target_fork_name, self.github_pr_number)
        # The following should be an invariant:
        assert self.github_pr_url == pr.github_pr_url
        # Create an instance if necessary:
        instance = self.instance or OpenEdXInstance()
        instance.sub_domain = 'pr{number}.sandbox'.format(number=pr.number)
        instance.base_domain = settings.INSTANCES_BASE_DOMAIN
        instance.edx_platform_repository_url = 'https://github.com/{pr.fork_name}.git'.format(pr=pr)
        instance.edx_platform_commit = pr.branch_tip_hash
        instance.name = (
            'PR#{pr.number}: {pr.truncated_title} ({pr.username}) - {pr.reference_name} ({commit_short_id})'
            .format(pr=pr, commit_short_id=instance.edx_platform_commit[:7])
        )
        instance.configuration_extra_settings = pr.extra_settings
        instance.use_ephemeral_databases = pr.use_ephemeral_databases(instance.domain)
        instance.configuration_source_repo_url = pr.get_extra_setting(
            'edx_ansible_source_repo', default=instance.configuration_source_repo_url
        )
        instance.configuration_version = pr.get_extra_setting(
            'configuration_version', default=instance.configuration_version
        )
        # Save atomically. (because if the instance gets created but self.instance failed to
        # update, then any subsequent call to update_instance_from_pr() would try to create
        # another instance, which would fail due to unique domain name constraints.)
        with transaction.atomic():
            instance.save()
            if not self.instance:
                self.instance = instance
                self.save(update_fields=["instance"])  # pylint: disable=no-member

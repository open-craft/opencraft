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

from instance.logging import ModelLoggerAdapter
from instance.models.openedx_instance import OpenEdXInstance, generate_internal_lms_domain
from pr_watch import github
from pr_watch.github import fork_name2tuple


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
    def get_or_create_from_pr(self, pr):
        """
        Get or create an instance for the given pull request
        """
        watched_pr, created = self.get_or_create(
            fork_name=pr.fork_name,
            branch_name=pr.branch_name,
            github_pr_url=pr.github_pr_url,
        )
        if created:
            watched_pr.update_instance_from_pr(pr)
        return watched_pr.instance, created

    def create(self, *args, **kwargs):
        """
        Augmented `create()` method:
        - Adds support for `fork_name` to allow to set both the github org & repo
        - Sets the github org & repo to `settings.DEFAULT_FORK` if any is missing
        - Sets the `commit_id` to the branch tip if it isn't explicitly passed as an argument
        """
        fork_name = kwargs.pop('fork_name', None)
        watched_pr = self.model(**kwargs)
        if fork_name is None and (not watched_pr.github_organization_name or not watched_pr.github_repository_name):
            fork_name = settings.DEFAULT_FORK
        if fork_name is not None:
            watched_pr.set_fork_name(fork_name)

        self._for_write = True
        watched_pr.save(force_insert=True, using=self.db)
        return watched_pr

    def get(self, *args, **kwargs):
        """
        Augmented `get()` method:
        - Adds support for `fork_name` to allow to query the github org & repo using a single argument
        """
        fork_name = kwargs.pop('fork_name', None)
        if fork_name is not None:
            kwargs['github_organization_name'], kwargs['github_repository_name'] = fork_name2tuple(fork_name)

        return super().get(*args, **kwargs)


class WatchedPullRequest(models.Model):
    """
    Represents a single watched pull request; holds the ID of the Instance created for that PR,
    if any
    """
    # TODO: Remove 'ref_type' ?
    # TODO: Remove parameters from 'update_instance_from_pr'; make it fetch PR details from the
    # api (including the head commit sha hash, which does not require a separate API call as
    # is currently used.)
    branch_name = models.CharField(max_length=50, default='master')
    ref_type = models.CharField(max_length=50, default='heads')
    github_organization_name = models.CharField(max_length=200, db_index=True)
    github_repository_name = models.CharField(max_length=200, db_index=True)
    github_pr_url = models.URLField(blank=False)
    instance = models.OneToOneField('instance.OpenEdXInstance', null=True, blank=True, on_delete=models.SET_NULL)

    objects = WatchedPullRequestQuerySet.as_manager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    @property
    def fork_name(self):
        """
        Fork name (eg. 'open-craft/edx-platform')
        """
        return '{0.github_organization_name}/{0.github_repository_name}'.format(self)

    @property
    def reference_name(self):
        """
        A descriptive name for the PR, which includes meaningful attributes
        """
        return '{0.github_organization_name}/{0.branch_name}'.format(self)

    @property
    def github_base_url(self):
        """
        Base GitHub URL of the fork (eg. 'https://github.com/open-craft/edx-platform')
        """
        return 'https://github.com/{0.fork_name}'.format(self)

    @property
    def github_branch_url(self):
        """
        GitHub URL of the branch tree
        """
        return '{0.github_base_url}/tree/{0.branch_name}'.format(self)

    @property
    def github_pr_number(self):
        """
        Get the PR number from the URL of the PR.
        """
        if not self.github_pr_url:
            return None
        return int(self.github_pr_url.split('/')[-1])

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

    def get_log_message_annotation(self):
        """
        Format a log message annotation for this PR.
        """
        if self.instance:
            return self.instance.get_log_message_annotation()
        return None

    def get_branch_tip(self):
        """
        Get the `commit_id` of the current tip of the branch
        """
        self.logger.info('Fetching commit ID of the tip of branch %s', self.branch_name)
        try:
            new_commit_id = github.get_commit_id_from_ref(
                self.fork_name,
                self.branch_name,
                ref_type=self.ref_type)
        except github.ObjectDoesNotExist:
            self.logger.error("Branch '%s' not found. Has it been deleted on GitHub?",
                              self.branch_name)
            raise

        return new_commit_id

    def set_fork_name(self, fork_name):
        """
        Set the organization and repository based on the GitHub fork name
        """
        assert not self.github_organization_name
        assert not self.github_repository_name
        self.logger.info('Setting fork name: %s', fork_name)
        fork_org, fork_repo = github.fork_name2tuple(fork_name)
        self.github_organization_name = fork_org
        self.github_repository_name = fork_repo

    def update_instance_from_pr(self, pr):
        """
        Update/create the associated sandbox instance with settings from the given pull request.

        This will not spawn a new AppServer.
        This method will automatically save this WatchedPullRequest's 'instance' field.
        """
        # The following fields should never change:
        assert self.github_pr_url == pr.github_pr_url
        assert self.fork_name == pr.fork_name
        assert self.branch_name == pr.branch_name
        # Create an instance if necessary:
        instance = self.instance or OpenEdXInstance()
        instance.internal_lms_domain = generate_internal_lms_domain('pr{number}.sandbox'.format(number=pr.number))
        instance.edx_platform_repository_url = self.repository_url
        instance.edx_platform_commit = self.get_branch_tip()
        instance.name = (
            'PR#{pr.number}: {pr.truncated_title} ({pr.username}) - {i.reference_name} ({commit_short_id})'
            .format(pr=pr, i=self, commit_short_id=instance.edx_platform_commit[:7])
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
                self.save(update_fields=["instance"])

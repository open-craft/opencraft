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
PR Watcher app models
"""

# Imports #####################################################################

import logging
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction

from instance.ansible import yaml_merge
from instance.logging import ModelLoggerAdapter
from instance.models.mixins.domain_names import generate_internal_lms_domain
from instance.models.openedx_instance import OpenEdXInstance

from userprofile.models import UserProfile, Organization

from pr_watch import github
from pr_watch.github import fork_name2tuple


# Logging #####################################################################

logger = logging.getLogger(__name__)

# Validators ##################################################################

sha1_validator = RegexValidator(regex='^[0-9a-f]{40}$', message='Full SHA1 hash required')


# Models ######################################################################

class WatchedFork(models.Model):
    """
    Represents a fork of edx/edx-platform whose PRs we watch.
    """
    # uses internal id key
    enabled = models.BooleanField(default=True)
    # This is the old .env variable WATCH_ORGANIZATION
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        help_text=(
            'Organization to watch. PRs against the watched fork made by members '
            'of this organization will trigger a sandbox build.'
        ),
    )
    # This is the old .env variable WATCH_FORK
    fork = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Github fork name that will be watched for PRs. E.g.: open-craft/edx-platform'
    )
    # This is equivalent to the DEFAULT_CONFIGURATION_REPO_URL .env variable
    configuration_source_repo_url = models.URLField(
        blank=True,
        null=True,
        help_text='If set, it overrides the default configuration repository',
    )
    # Equivalent to settings.DEFAULT_CONFIGURATION_VERSION
    configuration_version = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='If set, it overrides the default configuration version',
    )
    openedx_release = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text='If set, it overrides the the default Open edX release tag',
    )
    configuration_extra_settings = models.TextField(
        blank=True,
        null=False,
        default="",
        help_text=("YAML string with extra variables. These take precedence over the instance's default "
                   "extra settings, but can be overriden by the PR settings"),
    )

    class Meta:
        unique_together = ('organization', 'fork')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    def __str__(self):
        return "Fork {} ({})".format(self.fork, self.organization)


class WatchedPullRequestQuerySet(models.QuerySet):
    """
    Additional methods for WatchedPullRequest querysets
    Also used as the standard manager for the WatchedPullRequest model
    """
    def get_or_create_from_pr(self, pr, watched_fork=None):
        """
        Get or create an instance for the given pull request
        """
        created = False
        try:
            watched_pr = WatchedPullRequest.objects.get(fork_name=pr.fork_name,
                                                        branch_name=pr.branch_name,
                                                        github_pr_url=pr.github_pr_url,
                                                        watched_fork=watched_fork)

        except WatchedPullRequest.DoesNotExist:
            watched_pr = self.create(fork_name=pr.fork_name,
                                     branch_name=pr.branch_name,
                                     github_pr_url=pr.github_pr_url,
                                     watched_fork=watched_fork)
            watched_pr.save()
            created = True

        if created:
            watched_pr.update_instance_from_pr(pr)

        return watched_pr.instance, created

    def create(self, *args, **kwargs):  # pylint: disable=arguments-differ
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
    watched_fork = models.ForeignKey(WatchedFork, blank=True, null=True, on_delete=models.CASCADE)
    branch_name = models.CharField(max_length=255, default='master')
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
        is_external_pr = self.watched_fork is None
        instance.internal_lms_domain = generate_internal_lms_domain(
            '{prefix}pr{number}.sandbox'.format(
                prefix='ext' if is_external_pr else '',
                number=pr.number,
            )
        )
        instance.edx_platform_repository_url = self.repository_url
        instance.edx_platform_commit = self.get_branch_tip()
        instance.name = (
            '{prefix}PR#{pr.number}: {pr.truncated_title} ({pr.username}) - {i.reference_name} ({commit_short_id})'
            .format(
                pr=pr,
                i=self,
                commit_short_id=instance.edx_platform_commit[:7],
                prefix='EXT' if is_external_pr else '',
            )
        )
        if is_external_pr:
            instance.configuration_extra_settings = pr.extra_settings
        else:
            instance.configuration_extra_settings = yaml_merge(
                self.watched_fork.configuration_extra_settings,
                pr.extra_settings
            )
        if not instance.ref.creator or not instance.ref.owner:
            try:
                user = UserProfile.objects.get(github_username=pr.username)
                instance.ref.creator = user
                instance.ref.owner = user.organization
            except UserProfile.DoesNotExist:
                # PR is not associated with an Ocim user
                pass
        # Configuration repo and version and edx release follow this precedence:
        # 1) PR settings. 2) WatchedFork settings. 3) instance model defaults
        instance.configuration_source_repo_url = pr.get_extra_setting(
            'edx_ansible_source_repo',
            default=(
                (self.watched_fork and self.watched_fork.configuration_source_repo_url) or
                instance.configuration_source_repo_url
            )
        )
        instance.configuration_version = pr.get_extra_setting(
            'configuration_version', default=(
                (self.watched_fork and self.watched_fork.configuration_version) or
                instance.configuration_version
            )
        )
        instance.openedx_release = pr.get_extra_setting(
            'openedx_release', default=(
                (self.watched_fork and self.watched_fork.openedx_release) or
                instance.openedx_release
            )
        )
        # Save atomically. (because if the instance gets created but self.instance failed to
        # update, then any subsequent call to update_instance_from_pr() would try to create
        # another instance, which would fail due to unique domain name constraints.)
        with transaction.atomic():
            instance.save()
            if not self.instance:
                self.instance = instance
                self.save(update_fields=["instance"])

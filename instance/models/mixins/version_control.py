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
Instance app model mixins - Version Control
"""
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from instance import github
from instance.github import fork_name2tuple, get_username_list_from_team


# Validators ##################################################################

sha1_validator = RegexValidator(regex='^[0-9a-f]{40}$', message='Full SHA1 hash required')


# Models ######################################################################

class GitHubInstanceQuerySet(models.QuerySet):
    """
    Additional methods for instance querysets
    Also used as the standard manager for the GitHubInstance model
    """
    def update_or_create_from_pr(self, pr, sub_domain):
        """
        Create or update an instance for the given pull request
        """
        instance, created = self.get_or_create(
            sub_domain=sub_domain,
            fork_name=pr.fork_name,
            branch_name=pr.branch_name,
        )
        instance.update_from_pr(pr)
        instance.save()
        return instance, created

    def create(self, *args, **kwargs):
        """
        Augmented `create()` method:
        - Adds support for `fork_name` to allow to set both the github org & repo
        - Sets the github org & repo to `instance.default_fork` if any is missing
        - Sets the `commit_id` to the branch tip if it isn't explicitly passed as an argument
        """
        fork_name = kwargs.pop('fork_name', None)
        instance = self.model(**kwargs)
        if fork_name is None and (not instance.github_organization_name or not instance.github_repository_name):
            fork_name = instance.default_fork
        if fork_name is not None:
            instance.set_fork_name(fork_name, commit=False)
        if not instance.commit_id:
            instance.set_to_branch_tip(commit=False)
        if not instance.name:
            instance.name = instance.reference_name

        self._for_write = True
        instance.save(force_insert=True, using=self.db)
        return instance

    def get(self, *args, **kwargs):
        """
        Augmented `get()` method:
        - Adds support for `fork_name` to allow to query the github org & repo using a single argument
        """
        fork_name = kwargs.pop('fork_name', None)
        if fork_name is not None:
            kwargs['github_organization_name'], kwargs['github_repository_name'] = fork_name2tuple(fork_name)

        return super().get(*args, **kwargs)


class VersionControlInstanceMixin(models.Model):
    """
    Instances linked to a VCS, such as git
    """

    class Meta:
        abstract = True

    branch_name = models.CharField(max_length=50, default='master')
    ref_type = models.CharField(max_length=50, default='heads')
    commit_id = models.CharField(max_length=40, validators=[sha1_validator])

    @property
    def commit_short_id(self):
        """
        Short `commit_id`, limited to 7 characters like on GitHub
        """
        if not self.commit_id:
            return None
        return self.commit_id[:7]


class GitHubInstanceMixin(VersionControlInstanceMixin):
    """
    Instance linked to a GitHub repository
    """
    github_organization_name = models.CharField(max_length=200, db_index=True)
    github_repository_name = models.CharField(max_length=200, db_index=True)
    github_pr_url = models.URLField(blank=True)
    github_admin_organization_name = models.CharField(max_length=200, blank=True,
                                                      default=settings.DEFAULT_ADMIN_ORGANIZATION)

    objects = GitHubInstanceQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def default_fork(self):
        """
        Name of the fork to use by default, when no repository is specified
        """
        return NotImplementedError

    @property
    def fork_name(self):
        """
        Fork name (eg. 'open-craft/edx-platform')
        """
        return '{0.github_organization_name}/{0.github_repository_name}'.format(self)

    @property
    def reference_name(self):
        """
        A descriptive name for the instance, which includes meaningful attributes
        """
        return '{0.github_organization_name}/{0.branch_name} ({0.commit_short_id})'.format(self)

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

    @property
    def github_admin_username_list(self):
        """
        Returns the github usernames of this instance admins

        Admins are the members of the default team of the `github_admin_organization_name` org
        """
        if self.github_admin_organization_name:
            return get_username_list_from_team(self.github_admin_organization_name)
        else:
            return []

    def set_to_branch_tip(self, branch_name=None, ref_type=None, commit=True):
        """
        Set the `commit_id` to the current tip of the branch

        By default, save the instance object - pass `commit=False` to not save it
        """
        if branch_name is not None:
            self.branch_name = branch_name
        if ref_type is not None:
            self.ref_type = ref_type
        self.logger.info('Setting instance to tip of branch %s', self.branch_name)
        try:
            new_commit_id = github.get_commit_id_from_ref(
                self.fork_name,
                self.branch_name,
                ref_type=self.ref_type)
        except github.ObjectDoesNotExist:
            self.logger.error("Branch '%s' not found. Has it been deleted on GitHub?",
                              self.branch_name)
            raise

        if new_commit_id != self.commit_id:
            old_commit_short_id = self.commit_short_id
            self.commit_id = new_commit_id

            # Update the hash in the instance title if it is present there
            # TODO: Find a better way to handle this - include the hash dynamically?
            if self.name and old_commit_short_id:
                self.name = self.name.replace(old_commit_short_id, self.commit_short_id)

        if commit:
            self.save()

    def set_fork_name(self, fork_name, commit=True):
        """
        Set the organization and repository based on the GitHub fork name

        By default, save the instance object - pass `commit=False` to not save it
        """
        self.logger.info('Setting fork name: %s', fork_name)
        fork_org, fork_repo = github.fork_name2tuple(fork_name)
        if self.github_organization_name == fork_org \
                and self.github_repository_name == fork_repo:
            return

        self.github_organization_name = fork_org
        self.github_repository_name = fork_repo
        if commit:
            self.save()

    def update_from_pr(self, pr):
        """
        Update this instance with settings from the given pull request
        """
        self.name = ('PR#{pr.number}: {pr.truncated_title}' +
                     ' ({pr.username}) - {i.reference_name}').format(pr=pr, i=self)
        self.github_pr_url = pr.github_pr_url

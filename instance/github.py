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
GitHub Service API - Helper functions
"""

# Imports #####################################################################

import logging
import functools
import operator
import re

from django.conf import settings
from django.template.defaultfilters import truncatewords
import requests
import yaml


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

GH_HEADERS = {
    'Authorization': 'token {}'.format(settings.GITHUB_ACCESS_TOKEN),
    'Time-Zone': 'UTC',
}


# Functions ###################################################################

def get_object_from_url(url):
    """
    Send the request to the provided URL, attaching custom headers, and returns
    the deserialized object from the returned JSON.

    Raises ObjectDoesNotExist if github returns a 404 response.
    """
    logger.info('GET URL %s', url)
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code == 404:
        raise ObjectDoesNotExist('404 response from {0}'.format(url))
    r.raise_for_status()
    return r.json()


def fork_name2tuple(fork_name):
    """
    Converts a `fork_name` (eg. `'open-craft/edx-platform'`)
    to a `fork_tuple` (eg. `['open-craft', 'edx-platform']`)
    """
    return fork_name.split('/')


def get_commit_id_from_ref(fork_name, ref_name, ref_type='heads'):
    """
    Get the `commit_id` currently attached to a git reference
    """
    url = 'https://api.github.com/repos/{fork_name}/git/refs/{ref_type}/{ref_name}'.format(
        fork_name=fork_name,
        ref_type=ref_type,
        ref_name=ref_name,
    )
    return get_object_from_url(url)['object']['sha']


def get_settings_from_pr_body(pr_body):
    """
    Extract a settings string from a PR description body
    """
    m = re.search("..Settings..\r?\n+```[a-z]*\r?\n((?:.+\r?\n)*)```", pr_body)
    if m:
        return m.groups()[0]
    else:
        return ''


def is_pr_body_requesting_ephemeral_databases(pr_body, domain):
    """
    Return True if the PR body specified that the sandbox should use ephemeral
    databases, False if it specifies persistent databases, or None otherwise
    """
    escaped_domain = re.escape(domain)
    if re.search(r'{0}.*ephemeral databases?'.format(escaped_domain), pr_body):
        return True
    if re.search(r'{0}.*persistent databases?'.format(escaped_domain), pr_body):
        return False
    return None


def get_pr_by_number(pr_target_fork_name, pr_number):
    """
    Returns a PR object based on the reponse
    """
    r_pr = get_object_from_url('https://api.github.com/repos/{pr_target_fork_name}/pulls/{pr_number}'.format(
        pr_target_fork_name=pr_target_fork_name,
        pr_number=pr_number,
    ))
    pr_fork_name = r_pr['head']['repo']['full_name']
    pr_branch_name = r_pr['head']['ref']
    pr = PR(
        pr_number,
        pr_fork_name,
        pr_target_fork_name,
        pr_branch_name,
        r_pr['title'],
        r_pr['user']['login'],
        body=r_pr['body'],
    )
    return pr


def get_pr_list_from_username(user_name, fork_name):
    """
    Retrieve the current active PRs for a given user
    """
    q = 'is:open is:pr author:{author} repo:{repo}'.format(author=user_name, repo=fork_name)
    r_pr_list = get_object_from_url('https://api.github.com/search/issues?sort=created&q={}'.format(q))
    logger.debug('List of PRs received for user %s: %s', user_name, r_pr_list)

    pr_list = []
    for pr_dict in r_pr_list['items']:
        pr = get_pr_by_number(fork_name, pr_dict['number'])
        pr_list.append(pr)
    return pr_list


def get_team_from_organization(organization_name, team_name='Owners'):
    """
    Retrieve a team by organization & team name
    """
    url = 'https://api.github.com/orgs/{org}/teams'.format(org=organization_name)
    for team_dict in get_object_from_url(url):
        if team_dict['name'] == team_name:
            return team_dict
    raise KeyError(team_name)


def get_username_list_from_team(organization_name, team_name='Owners'):
    """
    Retrieve the usernames of a given team's members
    """
    team = get_team_from_organization(organization_name, team_name)
    url = 'https://api.github.com/teams/{team_id}/members'.format(team_id=team['id'])
    return [user_dict['login'] for user_dict in get_object_from_url(url)]


# Classes #####################################################################

class PR:
    """
    Representation of a GitHub Pull Request
    """
    # pylint: disable=too-many-arguments
    def __init__(self, number, source_fork_name, target_fork_name, branch_name, title, username, body=''):
        self.number = number
        self.fork_name = source_fork_name
        self.repo_name = target_fork_name
        self.branch_name = branch_name
        self.title = title
        self.username = username
        self.body = body

    @property
    def truncated_title(self):
        """
        This PR's title truncated to 4 words
        """
        return truncatewords(self.title, 4)

    @property
    def extra_settings(self):
        """
        Extra settings contained in the PR body
        """
        return get_settings_from_pr_body(self.body)

    def get_extra_setting(self, name, default=None):
        """
        Return the setting given by "name" from extra_settings.

        The name may be a dot-separated path to retrieve nested settings.
        """
        extra_settings_dict = yaml.load(self.extra_settings) or {}
        try:
            return functools.reduce(operator.getitem, name.split('.'), extra_settings_dict)
        except KeyError:
            return default

    @property
    def github_pr_url(self):
        """
        Construct the URL for the pull request
        """
        return 'https://github.com/{repo_name}/pull/{number}'.format(repo_name=self.repo_name, number=self.number)

    def use_ephemeral_databases(self, domain):
        """
        Does this PR request ephemeral databases?
        """
        return is_pr_body_requesting_ephemeral_databases(self.body, domain)


class ObjectDoesNotExist(Exception):
    """
    Exception raised when trying to access a github object that does not exist.
    """
    pass

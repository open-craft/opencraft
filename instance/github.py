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

import re
import requests

from collections import namedtuple
from django.conf import settings


# Constants ###################################################################

GH_HEADERS = {
    'Authorization': 'token {}'.format(settings.GITHUB_ACCESS_TOKEN),
}
PR = namedtuple('PR', 'name body number fork_name branch_name extra_settings')


# Functions ###################################################################

def get_fork_branch_name_for_pr(pr_from_json):
    """
    Get the branch name of a PR, from its JSON description returned by the API
    """
    fork_name = pr_from_json['head']['repo']['full_name']
    branch_name = pr_from_json['head']['ref']
    return [fork_name, branch_name]


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
    r = requests.get(url, headers=GH_HEADERS)
    r.raise_for_status()
    return r.json()['object']['sha']


def get_settings_from_pr_body(pr_body):
    """
    Extract a settings string from a PR description body
    """
    m = re.search("..Settings..\r?\n+```[a-z]*\r?\n((?:.+\r?\n)*)```", pr_body)
    if m:
        return m.groups()[0]
    else:
        return None


def get_pr_by_number(fork_name, pr_number):
    """
    Returns a PR() namedtuple based on the reponse
    """
    url = 'https://api.github.com/repos/{fork_name}/pulls/{pr_number}'.format(
        fork_name=fork_name,
        pr_number=pr_number,
    )
    r = requests.get(url, headers=GH_HEADERS)
    r.raise_for_status()

    r_pr = r.json()
    pr_fork_name, pr_branch_name = get_fork_branch_name_for_pr(r_pr)
    pr = PR(
        name='{pr[title]} ({pr[user][login]})'.format(pr=r_pr),
        number=pr_number,
        fork_name=pr_fork_name,
        branch_name=pr_branch_name,
        body=r_pr['body'],
        extra_settings=get_settings_from_pr_body(r_pr['body']),
    )
    return pr


def get_pr_list_for_user(user_name, fork_name):
    """
    Retreive the current active PRs for a given user
    """
    q = 'is:open is:pr author:{author} repo:{repo}'.format(author=user_name, repo=fork_name)
    url = 'https://api.github.com/search/issues?sort=created&q={}'.format(q)
    r = requests.get(url, headers=GH_HEADERS)

    pr_list = []
    for pr_dict in r.json()['items']:
        pr = get_pr_by_number(fork_name, pr_dict['number'])
        pr_list.append(pr)
    return pr_list


def get_team_for_organization_team_name(organization_name, team_name='Owners'):
    """
    Retreive a team by organization & team name
    """
    url = 'https://api.github.com/orgs/{org}/teams'.format(org=organization_name)
    r = requests.get(url, headers=GH_HEADERS)
    r.raise_for_status()

    for team_dict in r.json():
        if team_dict['name'] == team_name:
            return team_dict
    raise KeyError(team_name)


def get_user_name_list_for_organization_team(organization_name, team_name='Owners'):
    """
    Retreive the usernames of a given team's members
    """
    team = get_team_for_organization_team_name(organization_name, team_name)
    url = 'https://api.github.com/teams/{team_id}/members'.format(team_id=team['id'])
    r = requests.get(url, headers=GH_HEADERS)
    r.raise_for_status()
    return [user_dict['login'] for user_dict in r.json()]


def get_pr_list_for_organization_team(organization_name, fork_name, team_name='Owners'):
    """
    Retreive the active PRs of a given team in a fork
    """
    pr_list = []
    for user_name in get_user_name_list_for_organization_team(organization_name, team_name):
        pr_list.append(get_pr_list_for_user(user_name, fork_name))
    return pr_list


def get_watched_pr_list():
    """
    Retreive the active PRs of the teams & forks to be watched, from the settings
    """
    if not settings.WATCH_FORK or not settings.WATCH_ORGANIZATION:
        return []

    return get_pr_list_for_organization_team(
        settings.WATCH_ORGANIZATION,
        settings.WATCH_FORK)

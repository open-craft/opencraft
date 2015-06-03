import github3

from collections import namedtuple
from django.conf import settings


gh = github3.login(token=settings.GITHUB_ACCESS_TOKEN)


def get_branch_name_for_pr(pr_number):
    return 'pull/{}/head'.format(pr_number)

def fork_name2tuple(fork_name):
    return fork_name.split('/')

def get_pr_by_number(fork_name, pr_number):
    '''
    Returns a PR() namedtuple based on the github3 PullRequest object obtained from the API
    '''
    PR = namedtuple('PR', 'github3 name fork_name branch_name')

    repository_owner_name, repository_name = fork_name2tuple(fork_name)
    pr_github3 = gh.pull_request(repository_owner_name, repository_name, pr_number)

    pr_number = pr_github3.as_dict()['number']
    pr = PR(
        github3 = pr_github3.as_dict(),
        name = '{pr[title]} ({pr[user][login]})'.format(pr=pr_github3.as_dict()),
        fork_name = fork_name,
        branch_name = get_branch_name_for_pr(pr_number),
    )

    return pr

def get_pr_list_for_user(user_name, fork_name):
    pr_list = []
    for pr_github3 in gh.search_issues('is:open is:pr author:{} repo:{}'.format(user_name, fork_name)):
        pr_number = pr_github3.as_dict()['number']
        pr = get_pr_by_number(fork_name, pr_number)
        pr_list.append(pr)
    return pr_list

def get_team_for_organization_team_name(organization_name, team_name='Owners'):
    for team in gh.organization(organization_name).teams():
        if team.name == team_name:
            return team
    raise KeyError(team_name)

def get_user_name_list_for_organization_team(organization_name, team_name='Owners'):
    team = get_team_for_organization_team_name(organization_name, team_name)
    return [user.login for user in team.members()]

def get_pr_list_for_organization_team(organization_name, fork_name, team_name='Owners'):
    pr_list = []
    for user_name in get_user_name_list_for_organization_team(organization_name, team_name):
        pr_list += get_pr_list_for_user(user_name, fork_name)
    return pr_list

def get_watched_pr_list():
    if not settings.WATCH_FORK or not settings.WATCH_ORGANIZATION:
        return []

    return get_pr_list_for_organization_team(
        settings.WATCH_ORGANIZATION,
        settings.WATCH_FORK)

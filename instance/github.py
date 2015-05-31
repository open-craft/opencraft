from github3 import login

from django.conf import settings


gh = login(token=settings.GITHUB_ACCESS_TOKEN)


def get_branch_name_for_pr(pr_number):
    return 'pull/{}/head'.format(pr_number)

def get_pr_list_for_user(user_name, repository_name='edx/edx-platform'):
    return [pr for pr in gh.search_issues('is:open is:pr author:{} repo:{}'.format(user_name, repository_name))]

def get_team_for_organization_team_name(organization_name, team_name='Owners'):
    for team in gh.organization(organization_name).teams():
        if team.name == team_name:
            return team
    raise KeyError(team_name)

def get_user_name_list_for_organization_team(organization_name, team_name='Owners'):
    team = get_team_for_organization_team_name(organization_name, team_name)
    return [user.login for user in team.members()]

def get_pr_list_for_organization_team(organization_name, team_name='Owners'):
    pr_list = []
    for user_name in get_user_name_list_for_organization_team(organization_name, team_name):
        pr_list += get_pr_list_for_user(user_name)
    return pr_list

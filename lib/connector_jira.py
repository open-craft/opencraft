#!/usr/bin/env python

# Imports #####################################################################

from jira.client import JIRA
from pprint import pprint #pylint: disable=unused-import


# Functions ###################################################################

def print_separator():
    print('=' * 20)


# Classes #####################################################################

class JiraConnector(object):

    def __init__(self, host='https://openedx.atlassian.net/'):
        self.jira = JIRA(host)

    def get_comments(self, issue_id):
        issue = self.jira.issue(issue_id)

        for comment in issue.fields.comment.comments:
            yield '{author}: {body}'.format(
                author=comment.author.displayName,
                body=comment.body,
            )


# Main ########################################################################

if __name__ == '__main__':
    jira = JiraConnector()
    for c in jira.get_comments('SOL-768'):
        print(c)
        print_separator()

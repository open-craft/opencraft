# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <contact@opencraft.com>
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
Worker tasks for user-related features
"""

# Imports #####################################################################

import logging

from django.conf import settings
from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task
from mailchimp3 import MailChimp
from more_itertools import chunked

from userprofile.models import UserProfile


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################

@db_periodic_task(crontab(day='*/1', hour='2', minute='0'))
def add_trial_users_to_mailchimp_list():
    """
    Adds opted-in trial users to the MailChimp list.

    This task runs once per day.
    """
    emails_local = set(
        UserProfile.objects.filter(
            subscribe_to_updates=True,
        ).values_list(
            'user__email',
            flat=True,
        )
    )

    mailchimp_client = MailChimp(settings.MAILCHIMP_API_KEY)
    emails_mailchimp = set(
        member['email_address']
        for member in mailchimp_client.lists.members.all(
            settings.MAILCHIMP_LIST_ID_FOR_TRIAL_USERS,
            get_all=True,
            fields='members.email_address',
        )['members']
    )

    members_diff = (
        {
            'email_address': email,
            'status': action,
        }
        for emails_diff, action in (
            (emails_local - emails_mailchimp, 'subscribed'),
            (emails_mailchimp - emails_local, 'unsubscribed'),
        )
        for email in sorted(emails_diff)
    )

    for batch in chunked(members_diff, settings.MAILCHIMP_BATCH_SIZE):
        mailchimp_client.lists.update_members(settings.MAILCHIMP_LIST_ID_FOR_TRIAL_USERS, data={
            'members': batch,
            'update_existing': True,
        })

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
Worker tasks - Tests
"""

# Imports #####################################################################

from unittest.mock import patch

from django.conf import settings

from instance.tests.base import create_user_and_profile, TestCase
from userprofile import tasks


# Tests #######################################################################

class AddTrialUsersToMailchimpListTestCase(TestCase):
    """
    Test cases for the periodic task that adds opted-in trial users to the
    MailChimp list.
    """

    @patch('requests.auth.HTTPBasicAuth', return_value=None)
    @patch('mailchimp3.entities.listmembers.ListMembers.all')
    @patch('mailchimp3.entities.lists.Lists.update_members')
    def _check(
            self, mock_mailchimp_update_members, mock_mailchimp_list_members,
            mock_mailchimp_auth, emails_local, emails_mailchimp,
            expected_batched_updates, batch_size=10
    ):
        """
        Mocks the MailChimp API and then runs a specific test scenario.
        """
        emails_local_subscribed = []
        for email in emails_local:
            profile = create_user_and_profile(email, email).profile
            if 'unsubscribed' not in email:
                emails_local_subscribed.append(email)
                profile.subscribe_to_updates = True
                profile.save()

        mock_mailchimp_list_members.return_value = {
            'members': [{'email_address': email} for email in emails_mailchimp],
        }

        with self.settings(MAILCHIMP_BATCH_SIZE=batch_size):
            tasks.add_trial_users_to_mailchimp_list.call_local()

        self.assertEqual(mock_mailchimp_update_members.call_count, len(expected_batched_updates))
        for batch in expected_batched_updates:
            mock_mailchimp_update_members.assert_any_call(
                settings.MAILCHIMP_LIST_ID_FOR_TRIAL_USERS,
                data={
                    'members': [
                        {
                            'email_address': email,
                            'status': action,
                        }
                        for email, action in batch
                    ],
                    'update_existing': True,
                }
            )

    def test_mailchimp_empty(self):
        """
        When local has members and the MailChimp list is empty, test if all
        opted-in local members are transferred to MailChimp (as 'subscribed').
        """
        self._check( # pylint: disable=no-value-for-parameter
            emails_local=[
                'local1@subscribed.com',
                'local3@subscribed.com',
                'local4@unsubscribed.com',
                'local5@unsubscribed.com',
                'local2@subscribed.com',
            ],
            emails_mailchimp=[
            ],
            expected_batched_updates=[
                [
                    ('local1@subscribed.com', 'subscribed'),
                    ('local2@subscribed.com', 'subscribed'),
                    ('local3@subscribed.com', 'subscribed'),
                ],
            ],
        )

    def test_local_empty(self):
        """
        When local is empty and the MailChimp list has members, test if all
        existing MailChimp members are updated to 'unsubscribed'.
        """
        self._check( # pylint: disable=no-value-for-parameter
            emails_local=[
            ],
            emails_mailchimp=[
                'mailchimp1@subscribed.com',
                'mailchimp3@subscribed.com',
                'mailchimp2@subscribed.com',
            ],
            expected_batched_updates=[
                [
                    ('mailchimp1@subscribed.com', 'unsubscribed'),
                    ('mailchimp2@subscribed.com', 'unsubscribed'),
                    ('mailchimp3@subscribed.com', 'unsubscribed'),
                ],
            ],
        )

    def test_same(self):
        """
        When both local and the MailChimp list have the same set of opted-in
        members (irregardless of how they're ordered), test if no updates are
        performed.
        """
        self._check( # pylint: disable=no-value-for-parameter
            emails_local=[
                'local2@unsubscribed.com',
                'both1@subscribed.com',
                'both3@subscribed.com',
                'both2@subscribed.com',
                'local1@unsubscribed.com',
            ],
            emails_mailchimp=[
                'both3@subscribed.com',
                'both2@subscribed.com',
                'both1@subscribed.com',
            ],
            expected_batched_updates=[
            ],
        )

    def test_diff(self):
        """
        When local and the MailChimp list have a different set of members, test
        if all the necessary updates are performed:

        - opted-in local-only members are transferred to MailChimp (as 'subscribed')
        - opted-out members present on both services are updated to 'unsubscribed'
        - MailChimp-only members are updated to 'unsubscribed'
        """
        self._check( # pylint: disable=no-value-for-parameter
            emails_local=[
                'local2@unsubscribed.com',
                'both2@unsubscribed.com',
                'both1@subscribed.com',
                'local1@subscribed.com',
            ],
            emails_mailchimp=[
                'mailchimp1@subscribed.com',
                'both1@subscribed.com',
                'mailchimp2@unsubscribed.com',
                'both2@unsubscribed.com',
            ],
            expected_batched_updates=[
                [
                    ('local1@subscribed.com', 'subscribed'),
                    ('both2@unsubscribed.com', 'unsubscribed'),
                    ('mailchimp1@subscribed.com', 'unsubscribed'),
                    ('mailchimp2@unsubscribed.com', 'unsubscribed'),
                ],
            ],
        )

    def test_batched_updates(self):
        """
        With smaller sized MailChimp batched updates, when local has members and
        the MailChimp list is empty, test if all opted-in local members are
        transferred in small batches to MailChimp (as 'subscribed').
        """
        self._check( # pylint: disable=no-value-for-parameter
            emails_local=[
                'local7@subscribed.com',
                'local1@subscribed.com',
                'local3@subscribed.com',
                'local4@unsubscribed.com',
                'local6@subscribed.com',
                'local5@unsubscribed.com',
                'local2@subscribed.com',
            ],
            emails_mailchimp=[
            ],
            expected_batched_updates=[
                [
                    ('local1@subscribed.com', 'subscribed'),
                    ('local2@subscribed.com', 'subscribed'),
                ],
                [
                    ('local3@subscribed.com', 'subscribed'),
                    ('local6@subscribed.com', 'subscribed'),
                ],
                [
                    ('local7@subscribed.com', 'subscribed'),
                ],
            ],
            batch_size=2,
        )

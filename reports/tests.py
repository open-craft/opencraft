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
"""Tests module for the invoices reports"""

# Imports #####################################################################
from collections import defaultdict
from datetime import timedelta, datetime
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

import ddt

from instance.models.appserver import Status as AppServerStatus
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.base import WithUserTestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import WatchedForkFactory
from reports.helpers import (
    _normalize_date,
    generate_charge_details,
    generate_charges,
    generate_watched_forks_instances,
    get_billing_period,
    get_instance_charges,
)
from userprofile.factories import OrganizationFactory

# Tests #####################################################################


@ddt.ddt
class ReportViewTestCase(WithUserTestCase):
    """
    Tests for reports views functionality
    """
    url = 'reports:report'

    def setUp(self):
        super(ReportViewTestCase, self).setUp()

        self.username = 'user3'
        self.password = 'pass'
        self.organization = OrganizationFactory.create(
            name='Organization Name',
            github_handle='organization_github_handle'
        )

    @ddt.data(
        None,  # Anonymous User
        'user1',  # Normal User
        'user2',  # Staff User
        'user4',  # Sandbox user
    )
    def test_report_view_not_superuser(self, username):
        """
        Users who are not logged in or logged in but don't have
        superuser credentials should not be able to see the page.
        """
        invoice_url = reverse(self.url, kwargs={
            'organization': 'dummy_org',
            'year': '2018',
            'month': '9'
        })
        expected_redirect = '{}?next={}'.format(reverse('registration:login'), invoice_url)

        if username:
            self.client.login(username=username, password=self.password)

        response = self.client.get(invoice_url)
        self.assertRedirects(
            response, expected_redirect,
            status_code=302,
            target_status_code=200,
            msg_prefix=''
        )

    @ddt.data(
        '15',
        '0',
    )
    def test_report_view_wrong_dates(self, invalid_month):
        """
        Wrong dates indicates wrong user behavior, we're returning 400 response
        in such cases.
        """
        self.client.login(username=self.username, password=self.password)

        url = reverse(self.url, kwargs={
            'organization': self.organization.github_handle,
            'year': '2018',
            'month': invalid_month
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_report_view_no_organization(self):
        """
        No organization means no report, simply we're returning a 404 response.
        """
        wrong_org = {
            'organization': 'bad_org',
            'year': '2018',
            'month': '10'
        }

        self.client.login(username=self.username, password=self.password)

        url = reverse(self.url, kwargs=wrong_org)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_report_view_no_forks(self):
        """
        If an organization doesn't have a any foks then the total charges
        must be 0
        """
        self.client.login(username=self.username, password=self.password)

        url = reverse(self.url, kwargs={
            'organization': self.organization.github_handle,
            'year': '2018',
            'month': '10'
        })
        response = self.client.get(url)
        self.assertContains(response, 'TOTAL including all forks: 0 €')

    @mock.patch("reports.views.generate_charges")
    def test_report_view_good_behavior(self, generate_charges_mock):
        """
        Good behavior here should return a 200 response
        """
        self.client.login(username=self.username, password=self.password)
        url = reverse(self.url, kwargs={
            'organization': self.organization.github_handle,
            'year': '2018',
            'month': '10'
        })

        generate_charges_mock.return_value = ({}, 10)
        response = self.client.get(url)
        self.assertContains(response, 'TOTAL including all forks: 10 €')


@ddt.ddt
class ReportsHelpersTestCase(TestCase):
    """
    Tests for reports helpers functions
    """

    def setUp(self):
        with mock.patch(
                'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
                return_value=(1, True)
        ):
            self.appserver = make_test_appserver()
        self.organization = OrganizationFactory.create(
            name='Organization Name',
            github_handle='organization_github_handle'
        )

    @ddt.data(
        (2000, 1, 1, 0, 0, 0, 0),
        (2018, 5, 12, 10, 30, 20, 40),
        (2222, 12, 31, 23, 59, 59, 1000),
    )
    def test_normalize_date(self, date_parts):
        """
        Will test the default case and the edge cases to truncate the date.
        """
        year, month, day, hour, minute, second, microsecond = date_parts
        date = datetime(year, month, day=day, hour=hour, minute=minute, second=second, microsecond=microsecond)

        new_date = _normalize_date(date)
        expected_date = datetime(year, month, 1)  # Should keep the same year and month

        self.assertEqual(new_date, expected_date)

    def test_get_billing_period_future_billing_date(self):
        """
        If the invoice is for future month then no billing dates are expected
        to be returned.
        """
        invoice_month = timezone.now() + timedelta(weeks=13)
        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)
        self.assertIsNone(first_billing_day)
        self.assertIsNone(last_billing_day)

    def test_get_billing_period_future_created_server(self):
        """
        If the invoice is being generated for an appserver that's created after
        the invoice month then no dates must be generated.
        """
        invoice_month = self._generate_invoice_date(year=2017)
        self.appserver.created = self._generate_invoice_date(year=2018)
        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)
        self.assertIsNone(first_billing_day)
        self.assertIsNone(last_billing_day)

    def test_get_billing_period_terminated_server(self):
        """
        Tests the calculated billing dates (start, and end) for a given
        terminated appserver before the month of the invoice month.
        """
        invoice_month = self._generate_invoice_date(this_month=True)

        # The app server was created in the past and terminated before the billing start date
        created = invoice_month - timedelta(weeks=10)
        terminated = invoice_month - timedelta(weeks=7)

        self.appserver.created = created
        self.appserver.terminated = terminated
        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)

        self.assertIsNone(first_billing_day)
        self.assertIsNone(last_billing_day)

        # An invoice from the past
        invoice_month = timezone.make_aware(datetime(2016, 10, 3))
        # The app server was created in the past and terminated before the billing start date
        created = invoice_month - timedelta(weeks=10)
        terminated = invoice_month - timedelta(weeks=7)

        self.appserver.created = created
        self.appserver.terminated = terminated
        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)

        self.assertIsNone(first_billing_day)
        self.assertIsNone(last_billing_day)

    def test_get_billing_period_not_terminated_server(self):
        """
        This includes two cases, if we're still in the current month and the
        AppServer is still running, or if the invoice is for a previous month
        and the AppServer wasn't terminated during that month.
        """

        # We're issuing an invoice for the current month when appserver is still running.

        invoice_month = self._generate_invoice_date(this_month=True)
        self.appserver.created = invoice_month - timedelta(weeks=3)

        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)

        # First billing day will be the first day of this month.
        self.assertEqual(first_billing_day.date(), invoice_month.date())
        # Last billing day will be today as the month is still active.
        self.assertEqual(last_billing_day.date(), timezone.now().date())

        # We're issuing an invoice for a previous month when AppServer was running during the whole month

        invoice_month = self._generate_invoice_date(year=2017)
        next_month = datetime(invoice_month.year, invoice_month.month + 1, 1)
        last_day = next_month - timedelta(days=1)
        self.appserver.created = invoice_month - timedelta(weeks=6)

        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)

        # First billing day will be the first day of the generated month.
        self.assertEqual(first_billing_day.date(), invoice_month.date())
        # Last billing day will be the last day of the month.
        self.assertEqual(last_billing_day.date(), last_day.date())

    def test_get_billing_period_partial_month_server(self):
        """
        This method will test billing dates for given months when servers
        were only created in the middle of the month.
        """

        # This will test appservers that were started during the month
        # but kept running after the month is over.
        invoice_month = self._generate_invoice_date(2017, 9)
        self.appserver.created = invoice_month + timedelta(days=10)
        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)

        self.assertEqual(first_billing_day.date(), timezone.make_aware(datetime(2017, 9, 11)).date())
        self.assertEqual(last_billing_day.date(), timezone.make_aware(datetime(2017, 9, 30)).date())

        # This will test appservers that were started during the month
        # and terminated during the month.
        invoice_month = self._generate_invoice_date(2017, 9)
        self.appserver.created = invoice_month + timedelta(days=10)
        self.appserver.terminated = invoice_month + timedelta(days=20)
        first_billing_day, last_billing_day = get_billing_period(self.appserver, invoice_month)

        self.assertEqual(first_billing_day.date(), timezone.make_aware(datetime(2017, 9, 11)).date())
        self.assertEqual(last_billing_day.date(), timezone.make_aware(datetime(2017, 9, 21)).date())

    @override_settings(BILLING_RATE=5)
    @ddt.data(
        (datetime(2018, 1, 1), datetime(2018, 1, 31), 31),  # Full month.
        (datetime(2018, 1, 1), datetime(2018, 1, 15), 15),  # Started at the beginning, terminated in the middle.
        (datetime(2018, 1, 15), datetime(2018, 1, 31), 17),  # Started in the middle, terminated at the end.
        (datetime(2018, 1, 13), datetime(2018, 1, 16), 4),  # Started and terminated in the middle of the month.
    )
    @ddt.unpack
    @mock.patch('reports.helpers.get_billing_period')
    def test_generate_charge_details(self, start, end, expected_days, billing_dates_mock):
        """
        We need to make sure that the calculated charges and days are
        correct.

        :param start: The start date of the billing period.
        :param end: The end date of the billing period
        :param expected_days: The days we should bill the users based on the billing dates.
        :param billing_dates_mock: Billing dates mock.
        """
        billing_dates_mock.return_value = start, end

        charge_details = generate_charge_details(self.appserver, start)
        self.assertEqual(charge_details, {
            'name': self.appserver.name,
            'billing_start': start,
            'billing_end': end,
            'days': expected_days,
            'charge': settings.BILLING_RATE * expected_days,
        })

    @mock.patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def get_instance_charges_future_month(self, mock_consul):
        """
        Test that the instance will return empty charges and 0 total for its
        AppServers if the invoice month is in future.
        """
        invoice_month = self._generate_invoice_date(year=datetime.now().year + 1)
        appservers_charges, appservers_total = get_instance_charges(OpenEdXInstanceFactory(), invoice_month)
        self.assertEqual(appservers_charges, [])
        self.assertEqual(appservers_total, 0)

    @mock.patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @mock.patch('reports.helpers.generate_charge_details')
    def test_get_instance_charges(self, charges_details_mock, mock_consul):
        """
        Test that an instance is going to generate charges for all of its
        terminated and running appservers only and make sure that servers
        from other instances are not included in the subtotals, total, etc.
        """
        desired_instance = OpenEdXInstanceFactory()
        make_test_appserver(desired_instance, status=AppServerStatus.Running)
        make_test_appserver(desired_instance, status=AppServerStatus.Terminated)
        make_test_appserver(desired_instance, status=AppServerStatus.ConfigurationFailed)

        another_instance = OpenEdXInstanceFactory()
        make_test_appserver(instance=another_instance)

        invoice_month = self._generate_invoice_date()
        expected_charges_details = {
            'name': 'Mock AppServer charge',
            'billing_start': invoice_month,
            'billing_end': invoice_month,
            'days': 20,
            'charge': 12,
        }
        charges_details_mock.return_value = expected_charges_details
        appservers_charges, appservers_total = get_instance_charges(desired_instance, invoice_month)

        self.assertEqual(len(appservers_charges), 2)
        for charge in appservers_charges:
            self.assertEqual(charge, expected_charges_details)

        self.assertEqual(appservers_total, 2 * expected_charges_details['charge'])

    def test_generate_watched_forks_instances(self):
        """
        This will test that the method is able to return all of the watched
        forks' instances for a specific organization and not anything else.
        """
        fork1, fork2, fork3 = self._setup_watched_forks()
        watched_forks = generate_watched_forks_instances(self.organization)

        # Because the third fork doesn't have any instances, it's not going to be shown in the reports
        self.assertIsInstance(watched_forks, defaultdict)
        self.assertEqual(len(watched_forks), 2)

        # Watched Fork 1 has only two instances
        self.assertIsInstance(watched_forks[fork1], list)
        self.assertEqual(len(watched_forks[fork1]), 2)
        for instance in watched_forks[fork1]:
            self.assertIsInstance(instance, OpenEdXInstance)

        # Watched Fork 2 has only one instance
        self.assertIsInstance(watched_forks[fork2], list)
        self.assertEqual(len(watched_forks[fork2]), 1)
        for instance in watched_forks[fork2]:
            self.assertIsInstance(instance, OpenEdXInstance)

        # Watched Fork 3 has no instances
        self.assertIsInstance(watched_forks[fork3], list)
        self.assertEqual(len(watched_forks[fork3]), 0)

    @mock.patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @mock.patch('reports.helpers.get_instance_charges')
    def test_generate_charges(self, instance_charges_mock, mock_consul):
        """
        Make sure that we're able to generate charges for all of the appservers
        that belong to any fork under a given organization.
        The test here will pass if all forks with their AppServers are included
        in the billing data and each fork is associated with all charges that
        belong to its instances.
        :param instance_charges_mock: A mock for get_instance_charges function.
        """
        invoice_month = self._generate_invoice_date(2017)
        instance_charges = 22
        charges_mock = {
            'name': 'Mock AppServer',
            'billing_start': invoice_month,
            'billing_end': invoice_month,
            'days': 10,
            'charge': 31,
        }
        instance_charges_mock.return_value = ([charges_mock], instance_charges)
        watched_forks = {
            'fork1': [OpenEdXInstanceFactory() for _ in range(2)],
            'fork2': [OpenEdXInstanceFactory() for _ in range(1)],
        }

        appservers_charges, appservers_total = generate_charges(watched_forks, invoice_month)
        self.assertEqual(appservers_total, 3 * instance_charges)
        self.assertEqual(len(appservers_charges), 2)
        self.assertEqual(len(appservers_charges['fork1']['instances']), 2)
        self.assertEqual(len(appservers_charges['fork2']['instances']), 1)
        self.assertIn(str(charges_mock), str(appservers_charges['fork1']['instances']))
        self.assertIn(str(charges_mock), str(appservers_charges['fork2']['instances']))

    def _setup_watched_forks(self):
        """
        This is a helper method that will generate the mesh of forks,
        instances, and pull requests linked together
        """
        watched_fork1 = WatchedForkFactory.create(
            fork='fork/repo1',
            organization=self.organization
        )
        watched_fork2 = WatchedForkFactory.create(
            fork='fork/repo2',
            organization=self.organization
        )
        watched_fork3 = WatchedForkFactory.create(
            fork='fork/repo3',
            organization=self.organization
        )

        with mock.patch(
                'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
                return_value=(1, True)
        ):
            instance1 = OpenEdXInstanceFactory()
            instance2 = OpenEdXInstanceFactory()
            instance3 = OpenEdXInstanceFactory()

        WatchedPullRequest.objects.create(
            fork_name=watched_fork1.fork,
            branch_name='new-tag',
            ref_type='tag',
            watched_fork=watched_fork1,
            instance=instance1
        )
        WatchedPullRequest.objects.create(
            fork_name=watched_fork1.fork,
            branch_name='new-tag',
            ref_type='tag',
            watched_fork=watched_fork1,
            instance=instance2
        )
        WatchedPullRequest.objects.create(
            fork_name=watched_fork2.fork,
            branch_name='new-tag',
            ref_type='tag',
            watched_fork=watched_fork2,
            instance=instance3
        )
        WatchedPullRequest.objects.create(
            fork_name=watched_fork3.fork,
            branch_name='new-tag',
            ref_type='tag',
            watched_fork=watched_fork3,
            instance=None
        )

        return watched_fork1, watched_fork2, watched_fork3

    @staticmethod
    def _generate_invoice_date(year=datetime.now().year, month=1, this_month=False):
        """
        Generates a date for the given year and month which starts with
        the day 1.

        :param year: The year of the invoice.
        :param month: The month of the invoice.
        :param this_month: If provided will create an invoice date for the
                           current month of the year.
        :return: A timezone-aware datetime object.
        """
        if this_month:
            now = timezone.now()
            date = datetime(now.year, now.month, 1)
        else:
            date = datetime(year, month, 1)

        return timezone.make_aware(date)

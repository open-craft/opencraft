# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
Helpers functions for Invoices Reports
"""
import calendar

from datetime import timedelta
from collections import defaultdict

from django.conf import settings
from django.utils import timezone

from instance.models.appserver import AppServer
from pr_watch.models import WatchedPullRequest


def _normalize_date(date):
    """
    Manipulates the given date and normalizes it to a standard day in a month
    to help in generating and comparing billing periods.
    The standardization process keeps the values of year and month as is in the given
    date and defaults the following parameters to these values:
    day: 1, hour: 0, minute: 0, second: 0, and microsecond: 0.

    :param date: The date we want to normalize.
    :return: A normalized date that defaults to a specific day in the given month.
    """
    return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_billing_period(appserver, invoice_start_date):
    """
    Fetches the first and the last billing days in a given month for a given server.
    This can be tricky as there are a lot of cases to cover everything, but
    basically here are the general rules that we follow to generate this.

    * If the server terminated before this month then don't issue a usage report for it.
    * If the server started after this month then also don't issue a usage report for it.
    * Ignore the invoice if the month is in future.

    * If the server started before this month then the start date is the month start date.
    * If the server started in this month then the start date is server start date.

    * If the server is still running then the billing end day is:
        - Today if this is the current month and the server is not terminated yet.
        - The end of the billing month if the server terminated after that month.
        - The termination date of the server if it's terminated before the end of this month.

    :param appserver: An OpenEdxAppServer instance.
    :param invoice_start_date: The beginning of the month we want to fetch dates for.
    :return: A pair of first and last billing days of the month
    """
    today = timezone.now()
    invoice_start_date = _normalize_date(invoice_start_date)

    future_billing_month = invoice_start_date > today
    appserver_terminated_before = appserver.terminated and appserver.terminated < invoice_start_date
    appserver_created_after = _normalize_date(appserver.created) > invoice_start_date

    if future_billing_month or appserver_terminated_before or appserver_created_after:
        return None, None

    if _normalize_date(today) == invoice_start_date:
        end_of_month = today
    else:
        _, month_days = calendar.monthrange(invoice_start_date.year, invoice_start_date.month)
        end_of_month = invoice_start_date + timedelta(days=month_days - 1)

    terminated_after_billing_month = appserver.terminated and _normalize_date(appserver.terminated) > invoice_start_date
    if not appserver.terminated or terminated_after_billing_month:
        last_billing_day = end_of_month
    else:
        last_billing_day = appserver.terminated

    if appserver.created < invoice_start_date:
        first_billing_day = invoice_start_date
    else:
        first_billing_day = appserver.created

    return first_billing_day, last_billing_day


def generate_charge_details(appserver, invoice_start_date):
    """
    Generates all of the charges and their details in a given period for a
    specific AppServer
    :param appserver: An OpenEdxAppServer
    :param invoice_start_date: The beginning of the month we want to issue usages for.
    :return: A dictionary all charges details. Example:
                {
                    'name': 'AppServer 1',
                    'billing_start': 1 - 9 - 2018,
                    'billing_end': 30 - 9 - 2018,
                    'days': 30,
                    'charge': 300,
                }
    """
    days = 0
    charge = 0
    billing_start, billing_end = get_billing_period(appserver, invoice_start_date)

    if billing_start and billing_end:
        # Adding one to the days to include the first day
        days = billing_end.day - billing_start.day + 1
        charge = settings.BILLING_RATE * days

    return {
        'name': appserver.name,
        'billing_start': billing_start,
        'billing_end': billing_end,
        'days': days,
        'charge': charge,
    }


def get_instance_charges(instance, invoice_start_date):
    """
    Generates the charges for the given instance's terminated and running
    AppServers in the given period of the invoice date.
    :param instance: An openEdxInstance object
    :param invoice_start_date: The beginning of the month we want to issue usages for.
    :return: A pair of the AppServers total usage and a list of the AppServers
             usages details. Example:
                [
                    {
                        'name': 'AppServer 1',
                        'billing_start': 1 - 9 - 2018,
                        'billing_end': 30 - 9 - 2018,
                        'days': 30,
                        'charge': 300,
                    },
                    {
                        'name': 'AppServer 2',
                        'billing_start': 1 - 9 - 2018,
                        'billing_end': 10 - 9 - 2018,
                        'days': 10,
                        'charge': 200,
                    }
                ]
    """
    appservers_charges = []
    appservers_total = 0

    if invoice_start_date > timezone.now():
        return appservers_charges, appservers_total

    for server in instance.appserver_set.all():
        not_running = server.status != AppServer.Status.Running
        not_terminated = server.status != AppServer.Status.Terminated
        not_billable = not_running and not_terminated

        charge_details = generate_charge_details(server, invoice_start_date)
        if not_billable or charge_details['charge'] == 0:
            continue

        appservers_charges.append(charge_details)
        appservers_total += charge_details['charge']

    return appservers_charges, appservers_total


def generate_watched_forks_instances(organization):
    """
    Extracts all of the watched forks for a specific organization over time
    and the instances generated for its watched forks.
    :param organization: Organization object
    :return: A dictionary of the watched forks and their instances. Example:
            {
                'fork1': [instance 1, instance 2],
                'fork2': [instance 4, instance 7, instance 6],
            }
    """
    watched_forks = defaultdict(list)
    pull_requests = WatchedPullRequest.objects.filter(
        watched_fork__organization=organization
    ).select_related('watched_fork', 'instance')

    for pull_request in pull_requests:
        if pull_request.instance:
            watched_forks[pull_request.watched_fork].append(pull_request.instance)

    return watched_forks


def generate_charges(forks_instances, invoice_start_date):
    """
    Iterates over the forks and generate a detailed report for every AppServer
    under each fork and computes the total days consumed by each individual fork
    and by all forks together.
    :param forks_instances: A dictionary of forks and their instances.
    :param invoice_start_date: The beginning of the month we want to issue usages for.
    :return: A pair of the total days used by the given forks and a dictionary of
             each fork's usages (by instance). Example:
             {
                'fork1': {'instances': {}, 'total': 0},
                'fork2': {
                    'instances': {
                        'instance1': [
                            {
                                'name': 'AppServer 1',
                                'billing_start': 1 - 9 - 2018,
                                'billing_end': 30 - 9 - 2018,
                                'days': 30,
                                'charge': 300,
                            },
                            {
                                'name': 'AppServer 2',
                                'billing_start': 1 - 9 - 2018,
                                'billing_end': 10 - 9 - 2018,
                                'days': 10,
                                'charge': 200,
                            }
                        ],
                        'instance2': [
                            {
                                'name': 'AppServer 3',
                                'billing_start': 10 - 9 - 2018,
                                'billing_end': 11 - 9 - 2018,
                                'days': 1,
                                'charge': 15,
                            }
                        ],
                    },
                    'total': 515
                }
            }
    """
    billing_data = {}
    total = 0

    for fork, instances in forks_instances.items():
        billing_data[fork] = {
            'instances': {},
            'total': 0
        }

        for instance in instances:
            appservers_charges, appservers_total = get_instance_charges(instance, invoice_start_date)

            billing_data[fork]['instances'][instance.name] = appservers_charges
            billing_data[fork]['total'] += appservers_total
            total += appservers_total

    return billing_data, total

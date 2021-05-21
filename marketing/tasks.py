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
Worker tasks for marketing features
"""

# Imports #####################################################################

import logging
from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now
from django.db.models import Prefetch
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from marketing.models import Subscriber, EmailTemplate, SentEmail
from marketing.utils import render_and_dispatch_email


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

def get_eligible_subscribers_queryset(template: EmailTemplate):
    """
    Creates and returns a queryset for all eligible subscribers for
    the given template.

    For better understanding following is a timeline containing filter days
                   +-------------------+
    <start>--------|<gte>--1-day--<lt>|--------send-after-days----<now>--
                   +-------------------+
    Eligible subscribers are those which are created in our one day window

    Uses prefetch to reduce DB queries.
    """
    gte = now() - timedelta(days=template.send_after_days + 1)
    lt = now() - timedelta(days=template.send_after_days)
    eligible_subscribers = Subscriber.objects.filter(
        trial_started_at__gte=gte,
        trial_started_at__lt=lt,
        receive_followup=True
    ).select_related('user', 'user__betatestapplication', 'user__profile').prefetch_related(
        Prefetch(
            'user__sentemail_set',
            queryset=SentEmail.objects.filter(template=template),
            to_attr="sent_emails"
        )
    )
    return eligible_subscribers

# Tasks #######################################################################


@db_periodic_task(crontab(day='*', hour='1', minute='0'))
def send_followup_emails():
    """
    Sends all the configured followup emails.
    """
    mails_to_send = []
    active_templates = EmailTemplate.objects.filter(is_active=True)
    # Collect all the emails to send
    for template in active_templates:
        eligible_subscribers = get_eligible_subscribers_queryset(template)
        for subscriber in eligible_subscribers:
            # Send email only if not already sent
            if not subscriber.user.sent_emails:
                mails_to_send.append(
                    (template, subscriber)
                )

    # Try sending all the followup emails
    for args in mails_to_send:
        render_and_dispatch_email(*args)


@db_periodic_task(crontab(day_of_week="1", hour="1", minute="0"))
def prune_emails():
    """
    Prune sent emails to control the size of storage.
    """
    delete_after = settings.MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS
    lt = now() - timedelta(days=delete_after)
    delete_count, _ = SentEmail.objects.filter(sent_at__lt=lt).delete()
    logger.info("Purged %s followup email", delete_count)

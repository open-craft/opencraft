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
"""
Management command to delete old archived instances
"""

import logging
import traceback
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from instance.models.instance import InstanceReference

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    delete_archives management command class
    """
    help = 'Deletes instances archived more than X months ago.'

    def add_arguments(self, parser):
        """
        Adds optional and required command options.
        """
        parser.add_argument(
            'months', type=int, help='Number of months a instance must have been archived to be deleted.'
        )
        parser.add_argument(
            '-y', '--yes', action='store_true', help='No confirmation required. BE EXTRA CAREFUL.'
        )

    def handle(self, *args, **options):
        """
        Finds old archived instances
        """
        self.log('Starting delete_archived')
        yes = options.get('yes', False)
        months = options.get('months')
        cutoff = dt.now() - relativedelta(months=months)

        refs = InstanceReference.objects.filter(
            is_archived=True,
            modified__lte=cutoff
        ).order_by(
            'modified'
        )

        instance_count = refs.count()

        if not instance_count:
            self.log('No archived instances older than {} months found.'.format(months))
            return

        self.log('Found {} archived instances older than {} months...'.format(instance_count, months))
        for ref in refs:
            self.log('- {}: {}'.format(ref.name[:30], ref.instance.internal_lms_domain))

        # Get user confirmation and deletes archived instances
        if yes or self.confirm('Are you absolutely sure you want to delete these instances?'):
            archived_count = 0
            for ref in refs:
                self.log('Deleting {}...'.format(ref.instance.internal_lms_domain))
                if self.delete_instance(ref.instance):
                    archived_count += 1
            self.log(
                'Deleted {} archived instances older than {} months.'.format(
                    archived_count, months)
            )
        else:
            self.log('Cancelled')

    def delete_instance(self, instance):
        """
        Deletes a single OpenEdXInstance. If it fails for any reason, handle
        the exception and log it so other the instances can proceed.
        """
        try:
            # TODO Remove dry-run
            assert False
            instance.delete()
        except Exception:  # noqa
            tb = traceback.format_exc()
            message = 'Failed to delete {}.'.format(instance.internal_lms_domain)
            LOG.exception(message)
            self.log(self.style.ERROR(message))
            self.stdout.write(self.style.ERROR(tb))
            return False
        return True

    def confirm(self, message):
        """
        Get user confirmation.
        """
        self.stdout.write('{} [y/N]'.format(message))
        answer = input()
        return answer.lower().startswith('y')

    def log(self, message):
        """
        Shortcut to log messages with date and time
        """
        self.stdout.write('{} | {}'.format(
            dt.now().strftime('%Y-%m-%d %H:%M:%S'),
            message
        ))

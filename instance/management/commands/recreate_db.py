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
This management command will destroy and recreate an instance's edxapp database. This is to remediate issues
where an initial provision fails mid-migration and can't finish without starting the DB over.
"""

import logging
from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError

from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This management command will recreate the edxapp database for a specified instance.
    """
    help = (
        'Drop and recreate a database for an instance. The instance must have failed initial provisioning.'
    )

    def add_arguments(self, parser):
        """
        Add the arguments for the DB recreation command.
        """
        parser.add_argument(
            '--domain',
            help='Domain name of instance to recreate db for',
            required=True,
        )
        parser.add_argument(
            # Needless to say, this isn't forensically valid and is on the honor system. Check system logs if unsure.
            '--admin',
            help="The name of the admin (that is, your name) who is performing this operation",
            required=True,
        )
        parser.add_argument(
            '--reason',
            help="A written reason for why you're recreating the database.",
            required=True,
        )
        parser.add_argument(
            # Not calling this 'force' because we're not coding in the option to force the drop and creation of a
            # DB this way.
            '-y', '--yes',
            help="Don't prompt for confirmation.",
            action='store_true',
        )

    def handle(self, *args, **options):
        """
        Recreates the instance's DB.
        """
        domain = options['domain']
        try:
            instance = OpenEdXInstance.objects.get(
                internal_lms_domain__iexact=domain,
            )
        except OpenEdXInstance.DoesNotExist:
            raise CommandError(f'An instance with the domain name "{domain}" could not be found.')
        if instance.successfully_provisioned:
            raise CommandError(
                f'Cowardly refusing to drop the database of "{domain}", which has already '
                'successfully provisioned at least once.',
            )

        self.confirm(instance.internal_lms_domain, options)
        instance.logger.warn(dedent(
            f"""
            !!!
            ! Blowing away and recreating the edxapp database!
            ! Authorized by: {options['admin']}
            ! Reason: {options['reason']}
            !!!
            """
        ))
        instance.logger.info('Dropping edxapp database...')
        instance.drop_db('edxapp')
        instance.logger.info('DB Dropped. Recreating database...')
        instance.create_db('edxapp')
        instance.logger.info('DB Recreated successfully.')

    def confirm(self, internal_lms_domain, options):
        """
        Gets confirmation from the user, and raises if confirmation fails.
        """
        if options['yes']:
            return
        self.stdout.write(f'> We will drop the edxapp database for {internal_lms_domain} and recreate it.\n')
        self.stdout.write(f'> Your name: {options["admin"]}\n')
        self.stdout.write(f'> Reason for recreating the DB: {options["reason"]}\n')
        answer = input('Are you sure you want to continue? [yes/No]')
        if not answer.lower().startswith('y'):
            raise CommandError('Aborted.')

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
MySQL Cleanup Script

Cleans up all MySQL databases left behind from CI
"""

import logging
import re
from datetime import datetime
from urllib.parse import urlparse

import MySQLdb as mysql
from MySQLdb import Error as MySQLError


# Logging ####################################################################

logger = logging.getLogger('integration_cleanup')


# Functions ##################################################################

def _get_cursor(url):
    """
    Returns a cursor on the database
    """
    database_url_obj = urlparse(url)
    try:
        connection = mysql.connect(
            host=database_url_obj.hostname,
            user=database_url_obj.username or '',
            passwd=database_url_obj.password or '',
            port=database_url_obj.port or 3306,
        )
    except MySQLError as exc:
        logger.exception('Cannot get MySQL cursor: %s', exc)
        return None
    return connection.cursor()


# Classes ####################################################################

class MySqlCleanupInstance:
    """
    Handles the cleanup of old MySQL databases
    """
    def __init__(self, age_limit, url, domain, dry_run):
        """
        Set up variables needed for cleanup
        """
        self.age_limit = age_limit
        self.cleaned_up_hashes = []
        self.domain_suffix = domain.replace('.', '_')
        self.dry_run = dry_run
        self.cursor = _get_cursor(url)

    def _get_old_databases(self):
        """
        Returns a list of databases older than the age limit
        """
        if not self.cursor:
            logger.error('ERROR: Not connected to the database')
            return []

        query = """SELECT table_schema, MAX(create_time) AS create_time
            FROM information_schema.tables
            WHERE create_time <= DATE_SUB(NOW(), INTERVAL %(age_limit)s DAY)
            AND table_schema LIKE %(domain_filter)s
            GROUP BY table_schema ORDER BY create_time DESC"""
        params = {
            'age_limit': self.age_limit,
            'domain_filter': '%_{}_%'.format(self.domain_suffix)
        }
        try:
            self.cursor.execute(query, params)
        except MySQLError as exc:
            logger.exception('Unable to retrieve old databases: %s', exc)
            return []
        return self.cursor.fetchall()

    def run_cleanup(self):
        """
        Runs the cleanup of MySQL databases older than the age limit
        """
        logger.info("\n --- Starting MySQL Cleanup ---")

        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken.")

        databases = self._get_old_databases()
        logger.info('Found %d old databases', len(databases))

        for (database, create_date) in databases:
            # The regex match here serves a dual purpose: firstly, it acts as
            # an additional precaution against removing databases not related
            # to CI. Secondly, it allows us to gather the hashes of the removed
            # databases so they can be returned to the calling script and used
            # in DNS cleanup.
            logger.info('  > Considering database %s', database)
            instance_database_re = r'^([0-9a-f]{8})([_0-9a-z]+)?_%s' % (self.domain_suffix,)
            match = re.match(instance_database_re, database)
            if not match:
                logger.info(
                    '    * SKIPPING: Did not match expected format %r.',
                    instance_database_re
                )
                continue

            logger.info(
                '    * Dropping MySQL DB `%s` created at %s', database,
                datetime.strftime(create_date, '%Y-%m-%dT%H:%M:%SZ')
            )
            if not self.dry_run:
                try:
                    self.cursor.execute(
                        'DROP DATABASE IF EXISTS {}'.format(database)
                    )
                    self.cleaned_up_hashes.append(match.groups()[0])
                except MySQLError as exc:
                    logger.exception(
                        'Unable to remove MySQL DB: %s. %s', database, exc
                    )

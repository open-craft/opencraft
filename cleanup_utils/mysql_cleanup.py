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
    Handles the cleanup of old and integration MySQL databases and users.

    Examples:
        Deleting old integration databases:
        >>> mysql_cleanup = MySqlCleanupInstance(
        ...     age_limit=DEFAULT_AGE_LIMIT,
        ...     url=os.environ['DEFAULT_INSTANCE_MYSQL_URL'],
        ...     domain=os.environ['DEFAULT_INSTANCE_BASE_DOMAIN'],
        ...     drop_dbs_and_users=False,
        ...     dry_run=dry_run
        ... )
        >>> mysql_cleanup.run_cleanup()

        Deleting all databases and users created for integration tests.
        >>> mysql_cleanup = MySqlCleanupInstance(
        ...     age_limit=DEFAULT_AGE_LIMIT,
        ...     url=os.environ['DEFAULT_INSTANCE_MYSQL_URL'],
        ...     domain=os.environ['DEFAULT_INSTANCE_BASE_DOMAIN'],
        ...     drop_dbs_and_users=True,
        ...     dry_run=dry_run
        ... )
        >>> mysql_cleanup.drop_integration_dbs_and_users()
    """
    def __init__(self, age_limit, url, domain, drop_dbs_and_users, dry_run):
        """
        Set up variables needed for cleanup

        Args:
            age_limit (int): Age limit to filter older databases in hours.
            url (str): MySQL server url in the form mysql://[user]:[pwd]@[host]:[port]/
            domain_suffix (str): Domain suffix used to create databses.
            drop_dbs_and_users (bool): If `True` all DBs and users used in integration tests will be dropped.
            dry_run (bool): If it's `True` no actions will be commited to the server.
        """
        self.age_limit = age_limit
        self.cleaned_up_hashes = []
        self.domain_suffix = domain.replace('.', '_')
        self.drop_dbs_and_users = drop_dbs_and_users
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
            WHERE create_time <= DATE_SUB(NOW(), INTERVAL %(age_limit)s HOUR)
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

    def _get_integration_databases(self):
        """
        List of integration databases.
        """
        if not self.cursor:
            logger.error('ERROR: Not connected to the database')
            return []

        query = (
            "SELECT Db from mysql.db where Db REGEXP 'integration_{domain_suffix}'".format(
                domain_suffix=self.domain_suffix
            )
        )
        try:
            self.cursor.execute(query)
        except MySQLError as exc:
            logger.exception('Unable to retrieve integrations databases: %s', exc)
            return []
        return self.cursor.fetchall()

    def _get_db_users(self, hash_prefix):
        """
        List of users filtering on a hash prefix.

        Args:
            hash_prefix (str): Hash prefix used to filter users.

        Returs:
            [tuple]: List of tuples with usernames.
        """
        if not self.cursor:
            logger.error('ERROR: Not connected to the database')
            return []
        prefix = "{hash_prefix}\\_%%".format(hash_prefix=hash_prefix)
        try:
            self.cursor.execute("SELECT User from mysql.user where User like %(prefix)s", {"prefix": prefix})
        except MySQLError as exc:
            logger.exception('Unable to retrieve old databases: %s', exc)
            return []
        return self.cursor.fetchall()

    def _get_integration_users(self):
        """
        List of users used in integration tests.
        """
        if not self.cursor:
            logger.error('ERROR: Not connected to the database')
            return []

        try:
            self.cursor.execute(
                """SELECT User from mysql.user where
                    User LIKE '%\\_ecommerce' OR
                    User LIKE '%\\_dashboard' OR
                    User LIKE '%\\_xqueue' OR
                    User LIKE '%\\_edxapp' OR
                    User LIKE '%\\_notes' OR
                    User LIKE '%\\_notifier' OR
                    User LIKE '%\\_api' OR
                    User LIKE '%\\_discovery' OR
                    User LIKE '%\\_reports' OR
                    User LIKE '%\\_program' OR
                    User LIKE '%\\_migrate' OR
                    User LIKE '%\\_read_only' OR
                    User LIKE '%\\_admin'"""
            )
        except MySQLError as exc:
            logger.exception('Unable to retrieve integration users: %s', exc)
            return []
        return self.cursor.fetchall()

    def _drop_db(self, database):
        """
        Drop a single database.

        Args:
            database (str): Database name.
        """
        if not self.dry_run:
            try:
                self.cursor.execute(
                    'DROP DATABASE IF EXISTS `{}`'.format(database)
                )
            except MySQLError as exc:
                logger.exception(
                    'Unable to remove MySQL DB: %s. %s', database, exc
                )

    def _drop_user(self, username):
        """
        Drop a single username.

        Args:
            username (str): Username.
        """
        if not self.dry_run:
            try:
                self.cursor.execute('DROP USER `{username}`'.format(username=username))
            except MySQLError as exc:
                logger.exception('Unable to drop user: %s. %s', username, exc)

    def run_cleanup(self):
        """
        Runs the cleanup of MySQL databases older than the age limit
        """
        logger.info("\n --- Starting MySQL Cleanup ---")

        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken.")
        self.drop_old_dbs()
        if self.drop_dbs_and_users:
            self.drop_integration_dbs_and_users()

    def drop_old_dbs(self):
        """
        Drop databases older than `age_limit`.
        """
        databases = self._get_old_databases()
        logger.info('Found %d old databases', len(databases))

        for (database, create_date) in databases:
            # The regex match here serves a dual purpose: firstly, it acts as
            # an additional precaution against removing databases not related
            # to CI. Secondly, it allows us to gather the hashes of the removed
            # databases so they can be returned to the calling script and used
            # in DNS cleanup.
            logger.info('  > Considering database %s', database)
            instance_database_re = r'^([0-9a-f]{6,8})([_0-9a-z]+)?_%s_[a-z0-9\_]+' % (self.domain_suffix,)
            match = re.match(instance_database_re, database)
            if not match:
                logger.info(
                    '    * SKIPPING: Did not match expected format %r.',
                    instance_database_re
                )
                continue
            db_hash = match.groups()[0]
            logger.info(
                '    * Dropping MySQL DB %s created at %s', database,
                datetime.strftime(create_date, '%Y-%m-%dT%H:%M:%SZ')
            )
            self._drop_db(database)
            self.cleaned_up_hashes.append(db_hash)
            self.drop_db_users(db_hash)

    def drop_db_users(self, db_hash):
        """
        Drop DB Users based on hash prefix. When DBs and Users are created in integration tests
        the same hash prefix is used for the database and for each user. Based on this prefix
        we can also drop all users related to a database.

        Args:
            db_hash (str): Database hash prefix.
        """
        users = self._get_db_users(db_hash)
        for user in users:
            username = user[0]
            logger.info('   * Dropping MySQL User %s', username)
            self._drop_user(username)

    def drop_integration_dbs_and_users(self):
        """
        Drop every database and user used in integration tests.
        """
        dbs = self._get_integration_databases()
        for db in dbs:
            database = db[0]
            logger.info('    * Dropping MySQL Databse %s', database)
            self._drop_db(database)

        users = self._get_integration_users()
        for user in users:
            username = user[0]
            logger.info('   * Dropping MySQL User %s', username)
            self._drop_user(username)

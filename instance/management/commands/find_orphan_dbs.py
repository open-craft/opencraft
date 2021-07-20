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
Management command to find orphaned databases
"""
import logging
import traceback

from django.core.management.base import BaseCommand
import MySQLdb as mysql
import pymongo

from instance.models.database_server import MongoDBServer, MySQLServer
from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)

MONGO_SYSTEM_DBS = {"admin", "local", "config"}
MYSQL_SYSTEM_DBS = {"information_schema", "performance_schema", "sys", "mysql"}


class Command(BaseCommand):
    """
    find_orphan_dbs management command class
    """

    help = 'Finds orphaned databases and generates commands to drop them.'

    def add_arguments(self, parser):

        parser.add_argument(
            "--rm",
            help="Drop any databases found",
            action="store_true",
        )

        subparsers = parser.add_subparsers(
            title='db type',
        )
        mongo_parser = subparsers.add_parser(
            'mongo', help='Find orphaned MongoDB databases')
        mongo_parser.add_argument(
            '--exclude-dbs',
            help=(
                'MongoDB databases to ignore when checking for orphans.\n'
                'System dbs are always excluded.'
            ),
            nargs='+',
            type=str,
            default=set()
        )
        mongo_parser.set_defaults(func=self.find_mongo_orphans)

        mysql_parser = subparsers.add_parser(
            'mysql', help='Find orphaned MySQL databases')
        mysql_parser.add_argument(
            '--exclude-dbs',
            help=(
                'MySQL databases to ignore when checking for orphans.\n'
                'System dbs are always excluded.'
            ),
            nargs='+',
            type=str,
            default=set()
        )
        mysql_parser.set_defaults(func=self.find_mysql_orphans)

    def handle(self, *args, **options):
        options['func'](**options)

    def find_mongo_orphans(self, exclude_dbs: list, **kwargs) -> int:
        """
        Find orphaned databases in MongoDB.

        This searches each MongoDB instance known to OCIM
        and verifies every database is associated with an
        OpenEdxInstance.
        """
        self.stderr.write("Finding orphaned MongoDB databases...")

        exclude_dbs = set(exclude_dbs) | MONGO_SYSTEM_DBS
        LOG.debug("Excluding MongoDB dbs %s", exclude_dbs)

        for mongo_server in MongoDBServer.objects.all():
            self.stderr.write(f"Looking in {mongo_server}")

            try:
                mongo = pymongo.MongoClient(
                    host=mongo_server.hostname,
                    port=mongo_server.port,
                    username=mongo_server.username,
                    password=mongo_server.password,
                    connect=True
                )
                eligible_db_names = {
                    db['name'] for db in mongo.list_databases()
                    if db['name'] not in exclude_dbs
                }
            except pymongo.errors.ConnectionFailure:
                traceback.print_exc(file=self.stderr)
                self.stderr.write(
                    f"Failed to connect to {mongo_server}, trying next...")
                continue

            orphan_dbs = self._find_mongo_orphans(eligible_db_names)
            for db in orphan_dbs:
                if kwargs['rm'] and self.confirm(f"Are you sure you want to drop {db}"):
                    mongo.drop_database(db)
            self._print_orphans(
                "mongo",
                f"{mongo_server.hostname}:{mongo_server.port}",
                orphan_dbs
            )

    def _find_mongo_orphans(self, db_names):
        """
        Find which mongo db names are not associated with any OpenEdX instances.
        """
        orphan_dbs = set(db_names)
        for instance in OpenEdXInstance.objects.all():
            orphan_dbs -= set(instance.mongo_database_names)
        return orphan_dbs

    def _print_orphans(self, db_type, host, dbs):
        """
        Print a line for each database.
        """
        self.stdout.writelines([
            "\t".join((db_type, host, db))
            for db in dbs
        ])
        count = len(dbs)
        self.stderr.write(
            f"{count} orphaned {db_type} databases were found on {host}.")

    def find_mysql_orphans(self, exclude_dbs: list, **kwargs) -> int:
        """
        Find orphaned databases in MySQL.

        This searches each MySQL instance known to OCIM
        and verifies every database is associated with an
        OpenEdxInstance.
        """
        self.stderr.write("Finding orphaned MySQL databases...")
        exclude_dbs = set(exclude_dbs) | MYSQL_SYSTEM_DBS

        for mysql_server in MySQLServer.objects.all():
            self.stderr.write(f"Looking in {mysql_server}")
            try:
                mysql_con = mysql.connect(
                    host=mysql_server.hostname,
                    port=mysql_server.port,
                    user=mysql_server.username,
                    password=mysql_server.password,
                )
            except mysql.MySQLError:
                traceback.print_exc(file=self.stderr)
                self.stderr.write(
                    f"Failed to connect to {mysql_server}, trying next...")
                continue
            with mysql_con.cursor() as cursor:
                cursor.execute("show databases")
                eligible_db_names = {
                    db[0] for db in cursor.fetchall()
                    if db[0] not in exclude_dbs
                }
                orphans = self._find_mysql_orphans(eligible_db_names)
                for db in orphans:
                    if kwargs['rm'] and self.confirm(f"Are you sure you want to drop {db}"):
                        cursor.execute(f"drop database `{db}`")
                self._print_orphans(
                    "mysql",
                    f"{mysql_server.hostname}:{mysql_server.port}",
                    orphans
                )

    def _find_mysql_orphans(self, db_names):
        """
        Find which MySQL db names are not associated with any OpenEdX instances.
        """
        orphan_dbs = set(db_names)
        for instance in OpenEdXInstance.objects.all():
            orphan_dbs -= instance.mysql_database_names
        return orphan_dbs

    def confirm(self, message):
        """
        Get user confirmation.
        """
        self.stdout.write('{} [y/N]'.format(message))
        answer = input()
        return answer.lower().startswith('y')

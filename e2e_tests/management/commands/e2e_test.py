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
Django Command e2e_test for running e2e_tests
"""

from django.core.management.commands import test

from e2e_tests.frontend_server import start_react_server


class Command(test.Command):
    """
    Management command to run the e2e test.

    Start the frontend server and run the tests in e2e application.
    """

    def handle(self, *args, **options):
        httpd, _ = start_react_server()
        args = (*args, 'e2e_tests')
        try:
            super(Command, self).handle(*args, **options)
        finally:
            httpd.shutdown()

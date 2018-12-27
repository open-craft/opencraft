# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
Instance - Activity CSV unit tests
"""
# Imports #####################################################################

from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase


# Tests #######################################################################

class ActivityCSVTestCase(TestCase):
    """
    Test cases for the `activity_csv` management command.
    """
    def setUp(self):
        super().setUp()

    def test_no_instances(self):
        """
        Verify that the command correctly notifies the user that there are no active app servers.
        """
        out = StringIO()
        with self.assertRaises(SystemExit):
            call_command('activity_csv', stderr=out)
        self.assertIn('There are no active app servers', out.getvalue())

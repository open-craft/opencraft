# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
Logging - Tests
"""
from mock import patch
from instance.logging import DBHandler
from instance.tests.base import TestCase


class DummyObject:
    """
    Dummy object for testing forced lazy evaluation.
    """
    levelname = 'DEBUG'

    # pylint: disable=no-self-use
    def __unicode__(self):
        return u'Rendered'


class TestDBHandler(TestCase):
    """
    Test the DB Handler
    """
    @patch('instance.models.log_entry')
    def test_db_handler_text_eval(self, mock_create):
        """
        Make sure the text of the record is evaluated early before being sent to the logger.
        """
        with patch('instance.logging.DBHandler.format') as mock_format:
            handler = DBHandler()
            handler.emit(DummyObject())
            self.assertTrue(mock_format.called)
            self.assertTrue(mock_create.called_with('debug', u'Rendered'))

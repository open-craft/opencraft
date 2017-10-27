# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Tests Django Widgets
"""
import re

from instance.tests.base import TestCase
from instance.widgets import JSONWidget


class JSONWidgetTestCase(TestCase):
    """
    Tests the JSONWidget class.
    """

    def setUp(self):
        self.html_front = re.compile(r'^.+?\>')
        self.html_back = re.compile(r'\<.+?\>$')

    def _strip_html(self, html_text):
        """
        Strips the front and end off an HTML string.
        """
        front_match = self.html_front.search(html_text).group()
        back_match = self.html_back.search(html_text).group()
        cleaned = html_text.replace(front_match, '')
        cleaned = cleaned.replace(back_match, '')
        return cleaned

    def test_render_string_json(self):
        """
        Tests rendering a string into json.
        """
        data = '{"valid": "json"}'
        widget = JSONWidget()
        result = widget.render("test", data)
        cleaned = self._strip_html(result)
        expected = '\r\n{&quot;valid&quot;: &quot;json&quot;}'
        self.assertEqual(expected, cleaned)

    def test_render_dict_json(self):
        """
        Tests rendering a python dictionary into json.
        """
        data = {"valid": "json"}
        widget = JSONWidget()
        result = widget.render("test", data)
        cleaned = self._strip_html(result)
        expected = '\r\n{&quot;valid&quot;: &quot;json&quot;}'
        self.assertEqual(expected, cleaned)

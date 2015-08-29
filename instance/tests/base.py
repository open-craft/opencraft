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
Tests - Base Class & Utils
"""

# Imports #####################################################################

import json
import os.path
import re

from django.contrib.auth.models import User
from django.test import Client, TestCase as DjangoTestCase


# Functions ###################################################################

def get_fixture_filepath(fixture_filename):
    """
    Returns the file path (including filename) for a fixture filename
    """
    current_directory = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_directory, 'fixtures', fixture_filename)


def get_raw_fixture(fixture_filename):
    """
    Returns the raw contents of a fixture, by filename
    """
    fixture_filepath = get_fixture_filepath(fixture_filename)
    with open(fixture_filepath) as f:
        return f.read()


def get_fixture(fixture_filename):
    """
    Returns the fixture object, by filename
    """
    fixture_filepath = get_fixture_filepath(fixture_filename)
    with open(fixture_filepath) as f:
        return json.load(f)


def add_fixture_to_object(obj, fixture_filename):
    """
    Load a fixture on an existing object
    """
    fixture = get_fixture(fixture_filename)
    obj.__dict__.update(fixture)
    return obj


# Classes #####################################################################

class AnyStringMatching(str):
    """
    String that matches any other string containing it

    Can be used to do partial argument matching in mock calls
    """
    def __eq__(self, other):
        return re.search(str(self), other)


# Tests #######################################################################

class TestCase(DjangoTestCase):
    """
    Base class for instance tests
    """
    def setUp(self):
        super().setUp()
        self.maxDiff = None #pylint: disable=invalid-name


class WithUserTestCase(DjangoTestCase):
    """
    Base class for instance tests
    """
    def setUp(self):
        super().setUp()

        self.client = Client()

        self.user1 = User.objects.create_user('user1', 'user1@example.com', 'pass')
        self.user1.save()

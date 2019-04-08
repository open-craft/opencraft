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
Tests - Base Class & Utils
"""

# Imports #####################################################################

import json
import os.path
import re

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase as DjangoTestCase

from userprofile.models import UserProfile, Organization
from ..models.instance import InstanceReference


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


def create_user_and_profile(username, email, password='pass', organization=None):
    """
    Create User and corresponding UserProfile.
    """
    user = User.objects.create_user(username, email, password)
    UserProfile.objects.create(
        full_name="Test User",
        user=user,
        organization=organization,
        github_username=username,
    )
    return user


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
        self.maxDiff = None


class WithUserTestCase(DjangoTestCase):
    """
    Base class for instance tests
    """

    def setUp(self):
        super().setUp()

        # Create admin organization
        self.organization = Organization.objects.create(
            name="test-org",
            github_handle="test"
        )

        # User1 is a basic user (no extra privileges: can't log in to admin, can't manage instances)
        # It could be a beta test user (whose organization we have manually written)
        self.user1 = create_user_and_profile(
            'user1',
            'user1@example.com',
            organization=self.organization
        )

        # User2 is a Staff member
        self.user2 = create_user_and_profile(
            'user2',
            'user2@example.com',
            organization=self.organization
        )
        self.user2.is_staff = True
        self.user2.save()

        # User3 is a superuser and therefore can manage all instances
        # Being a superuser, no other permission is required (not even manage_own)
        self.user3 = create_user_and_profile(
            'user3',
            'user3@example.com',
            organization=self.organization
        )
        self.user3.is_staff = True
        self.user3.is_superuser = True
        self.user3.save()

        # User 4 is a sandbox user, an instance manager (with permission to manage only their own instances)
        # Note that staff permission is not required to manage instances
        self.organization2 = Organization.objects.create(
            name="test-org-not-admin",
            github_handle="test-not-admin",
        )
        self.user4 = create_user_and_profile(
            'user4',
            'user4@example.com',
            organization=self.organization2
        )
        content_type = ContentType.objects.get_for_model(InstanceReference)
        permission = Permission.objects.get(
            content_type=content_type, codename='manage_own')
        self.user4.user_permissions.add(permission)
        self.user4.save()

        # User 5 has no organization (this isn't a common case).
        # Even with the explicit permission to manage their own instances,
        # this user shouldn't be able to see any instance.
        self.user5 = create_user_and_profile(
            'user5',
            'user5@example.com'
        )
        self.user5.user_permissions.add(permission)
        self.user5.save()

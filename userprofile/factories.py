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
Test factory: User, UserProfile, Organization
"""

from factory.django import DjangoModelFactory

from django.contrib.auth.models import User

from userprofile.models import UserProfile, Organization


class UserFactory(DjangoModelFactory):
    """
    Factory for User
    """

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = "edx"


class UserProfileFactory(DjangoModelFactory):
    """
    Factory for UserProfile
    """
    class Meta:
        model = UserProfile
        django_get_or_create = ('github_username',)

    full_name = "Test user"


class OrganizationFactory(DjangoModelFactory):
    """
    Factory for Organization
    """

    class Meta:
        model = Organization
        django_get_or_create = ('github_handle',)

    name = "Test org"
    github_handle = "test-org"


def make_user_and_organization(username="testuser", org_name="Test Org", org_handle="test-org", github_username="edx"):
    """
    Create User, UserProfile and Organization to reference from individual
    instances.

    :param username: The username of the User to create.
    :param org_name: The name of the Organization to create. (The user to
           create will be added to that organization.)
    :param org_handle: The GitHub handle of the organization to create.
    :param github_username: The GitHub username of the user to create.
    :return: A tuple consisting of the created UserProfile and Organization.
    """
    user = UserFactory(username=username)
    organization = OrganizationFactory(
        name=org_name,
        github_handle=org_handle
    )
    user_profile = UserProfileFactory(
        organization=organization,
        user=user,
        github_username=github_username
    )
    return user_profile, organization

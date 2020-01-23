# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
User-related models
"""

# Imports #####################################################################

from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance.models.utils import ValidateModelMixin


# Models ######################################################################


class Organization(ValidateModelMixin, TimeStampedModel):
    """
    Organizations model
    """
    name = models.CharField(max_length=255)
    github_handle = models.CharField(unique=True, null=True, blank=True, max_length=255)

    def __str__(self):
        return self.name


class UserProfile(ValidateModelMixin, TimeStampedModel):
    """
    Profile information for users.
    """
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    github_username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.CASCADE)
    accepted_privacy_policy = models.DateTimeField(
        verbose_name='Accept privacy policy',
        blank=True,
        null=True,
        help_text=('Date the user accepted the privacy policy.'),
    )
    accept_paid_support = models.BooleanField(
        default=False,
        help_text=('User understands that they may email OpenCraft for support, '
                   'and that such emails are subject to hourly fees.'),
    )
    subscribe_to_updates = models.BooleanField(
        default=False,
        help_text=('I want OpenCraft to keep me updated about important news, '
                   'tips, and new features, and occasionally send me an email about it.'),
    )

    def __str__(self):
        return self.full_name

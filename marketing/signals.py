# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <xavier@opencraft.com>
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
Signals related to marketing.
"""
from django.dispatch import receiver

from registration.signals import betatestapplication_accepted
from marketing.models import Subscriber


@receiver(betatestapplication_accepted)
def register_subscriber(sender, **kwargs):
    """
    Registers a marketing email subscriber for Beta testers
    on first successful appserver spawn. Only registers if user is not
    already registered as subscriber.
    """

    application = kwargs['application']


    Subscriber.objects.get_or_create(user_id=application.user.id)

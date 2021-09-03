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

from instance.signals import appserver_spawned
from marketing.models import Subscriber


@receiver(appserver_spawned)
def register_subscriber(sender, **kwargs):
    """
    Registers a marketing email subscriber for Beta testers
    on first successful appserver spawn. Only registers if user is not
    already registered as subscriber.
    """
    instance = kwargs['instance']
    appserver = kwargs['appserver']
    application = instance.betatestapplication_set.first()  # There should only be one

    # Ignore if the appserver was not spawned for a beta tester.
    if not application:
        return
    # Ignore if appserver didn't provision
    elif appserver is None:
        return
    else:
        # Register the user as followup email subscriber
        Subscriber.objects.get_or_create(user_id=application.user.id)

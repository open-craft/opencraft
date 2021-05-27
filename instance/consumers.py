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
Websocket consumers
"""

import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from instance.models.instance import InstanceReference


class WebSocketListener(WebsocketConsumer):
    """
    A websocket consumer for sending notifications.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_group_name = 'ws'

    def connect(self):
        user = self.scope['user']
        if not user.is_authenticated or not InstanceReference.can_manage(user):
            self.close()

        async_to_sync(self.channel_layer.group_add)(
            self.channel_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):  # pylint: disable=arguments-differ
        async_to_sync(self.channel_layer.group_discard)(
            self.channel_group_name,
            self.channel_name
        )

    def notification(self, event):
        """
        Handles the messages of type 'notification' sent to the self.channel_group_name group.
        """
        self.send(text_data=json.dumps(event))

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

# We need absolute_import to prevent ansible's json callback module from
# shadowing the python built-in json module.
from __future__ import absolute_import
import json
from ansible.plugins.callback.default import CallbackModule as DefaultCallback

class CallbackModule(DefaultCallback):
    """
    Ansible callback module which tweaks the default ansible output to make it more reable.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'prettify'

    def _get_item_label(self, result):
        """
        Overrides the DefaultCallback's `_get_item_label` method to returned a readable
        json representation of the item instead of a raw python dump.
        """
        item = super(CallbackModule, self)._get_item_label(result)
        return json.dumps(item, indent=2, ensure_ascii=False)

    def _dump_results(self, result, indent=2, sort_keys=False, keep_invocation=False):
        """
        Overrides the DefaultCallback's `_dump_results` to indent the json output by default.
        """
        return super(CallbackModule, self)._dump_results(
            result,
            indent=indent,
            sort_keys=sort_keys,
            keep_invocation=keep_invocation
        )

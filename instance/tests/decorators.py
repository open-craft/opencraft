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
Decorators - Useful decorators for unit tests
"""
from functools import wraps
from unittest import mock


def patch_git_checkout(func):
    """
    Patch git checkout process in order to allow mocking up the checkout
    process and the working directory
    """
    @wraps(func)
    def _wrap(*args, **kwargs):
        """
        Calls the given function with extra parameters for git checkout
        mocking
        """
        with mock.patch('git.refs.head.Head.checkout') as checkout:
            with mock.patch('git.Git.working_dir',
                            new_callable=mock.PropertyMock) as wd:
                return func(git_checkout=checkout, git_working_dir=wd,
                            *args, **kwargs)
    return _wrap

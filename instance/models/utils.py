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
Models Utils
"""


# Classes #####################################################################

class ValidateModelMixin(object):
    """
    Make :meth:`save` call :meth:`full_clean`.

    .. warning:
        This should be the left-most mixin/super-class of a model.

    More info:

    * "Why doesn't django's model.save() call full clean?"
        http://stackoverflow.com/questions/4441539/
    * "Model docs imply that ModelForm will call Model.full_clean(),
        but it won't."
        https://code.djangoproject.com/ticket/13100

    https://gist.github.com/glarrain/5448253
    """
    def save(self, *args, **kwargs):
        """Call :meth:`full_clean` before saving."""
        self.full_clean()
        super(ValidateModelMixin, self).save(*args, **kwargs)

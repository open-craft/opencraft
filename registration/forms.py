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
Forms for registration/login
"""

# Imports #####################################################################

import logging

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from djng.forms import NgDeclarativeFieldsMetaclass, NgFormValidationMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Widgets #####################################################################

class InputStyleMixin:
    """
    Adds the required styles to input fields.
    """
    css_classes = 'input input--host'

    def __init__(self, *args, **kwargs):
        """
        Set this widget's class attribute.
        """
        super().__init__(*args, **kwargs)
        self.attrs.setdefault('class', self.css_classes)


class TextInput(InputStyleMixin, forms.widgets.TextInput):
    """
    Adds styles to text input fields.
    """


class URLInput(InputStyleMixin, forms.widgets.URLInput):
    """
    Adds styles to URL fields.
    """


class EmailInput(InputStyleMixin, forms.widgets.EmailInput):
    """
    Adds styles to email input fields, and enables email validation.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['validate-email'] = True


class PasswordInput(InputStyleMixin, forms.widgets.PasswordInput):
    """
    Adds styles to password fields.
    """


class Textarea(InputStyleMixin, forms.widgets.Textarea):
    """
    Adds styles to textareas.
    """
    css_classes = 'textarea textarea--host'


# Forms #######################################################################

class LoginForm(NgFormValidationMixin, AuthenticationForm, metaclass=NgDeclarativeFieldsMetaclass):
    """
    Allows users to login with username/email and password.
    """
    username = forms.CharField(
        label='Your email or username',
        help_text='You can enter either your username or your email to login.',
        widget=TextInput,
    )
    password = forms.CharField(
        help_text=('If you have forgotten your login details or need to reset '
                   'your password, please '
                   '<a href="mailto:contact@opencraft.com">contact us</a>.'),
        strip=False,
        widget=PasswordInput,
    )

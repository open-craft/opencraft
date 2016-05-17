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
Forms for the Instance Manager beta test
"""

# Imports #####################################################################

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import capfirst
from djng.forms import NgDeclarativeFieldsMetaclass, NgFormValidationMixin, NgModelForm, NgModelFormMixin
from zxcvbn import password_strength

from registration.models import BetaTestApplication
from userprofile.models import UserProfile


# Forms #######################################################################

class BetaTestApplicationForm(NgModelFormMixin, NgFormValidationMixin, NgModelForm):
    """
    Application form for beta testers. Creates instances of User, UserProfile,
    and BetaTestApplication models on submit.
    """
    class Meta:
        model = BetaTestApplication
        exclude = ('user', 'status')
        widgets = {
            'public_contact_email': forms.widgets.EmailInput(attrs={
                'validate-email': True,
            }),
        }

    # Fields that can be modified after the application has been submitted
    can_be_modified = {
        'full_name',
        'project_description',
        'subscribe_to_updates',
    }

    full_name = forms.CharField(
        max_length=255,
        help_text='Example: Albus Dumbledore',
    )
    username = forms.RegexField(
        regex=r'^[\w.+-]+$',
        max_length=30,
        help_text=('This would also be the username of the administrator '
                   'account on the Open edX instance.'),
        error_messages={
            'invalid': ('Usernames may contain only letters, numbers, and '
                        './+/-/_ characters.'),
            'unique': 'This username is already taken.',
        },
    )
    email = forms.EmailField(
        help_text=('This is also your account name, and where we will send '
                   'important notices.'),
        widget=forms.widgets.EmailInput(attrs={'validate-email': True}),
    )
    password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput,
        help_text=('Pick a password for your OpenCraft account. You will be '
                   'able to use it to login and access your account.'),
    )
    password_confirmation = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput,
        help_text=('Please use a strong password: avoid common patterns and '
                   'make it long enough to be difficult to crack.'),
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='',
        help_text=('I understand that this is a beta test, that bugs and '
                   'crashes are expected, and that the instance is provided '
                   'for free for the duration of the beta-test, without any '
                   'guarantee.'),
        error_messages={
            'required': 'You must accept these terms to register.',
        },
    )

    # This field is created automatically from the model field, but the regex
    # validator is not copied over. We need to define the field manually so
    # that validation will work client-side. We do this by copying from the
    # model field (DRY).
    _subdomain_field = Meta.model._meta.get_field('subdomain')
    _subdomain_validator = next(v for v in _subdomain_field.validators
                                if hasattr(v, 'regex'))
    subdomain = forms.RegexField(
        regex=_subdomain_validator.regex,
        max_length=_subdomain_field.max_length,
        label=capfirst(_subdomain_field.verbose_name),
        help_text=_subdomain_field.help_text,
        error_messages={
            'invalid': _subdomain_validator.message,
        },
    )

    # Form values will be available in the angular scope under this namespace
    scope_prefix = 'registration'

    # This form itself will be available in the angular scope under this name
    form_name = 'form'

    def __init__(self, *args, **kwargs):
        """
        If this form updates an existing application, populate fields from
        related models and make non-modifiable fields read only.
        """
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial.update({
                'full_name': self.instance.user.profile.full_name,
                'username': self.instance.user.username,
                'email': self.instance.user.email,
                'accept_terms': True,
            })
            for name, field in self.fields.items():
                if name not in self.can_be_modified:
                    field.widget.attrs['readonly'] = True

    def clean_subdomain(self):
        """
        Strip the base domain from the end of the subdomain, if given.
        """
        subdomain = self.cleaned_data.get('subdomain')
        if subdomain:
            match = subdomain.rfind('.' + BetaTestApplication.BASE_DOMAIN)
            if match != -1:
                return subdomain[:match]
        return subdomain

    def clean_username(self):
        """
        Check that the username is unique.
        """
        username = self.cleaned_data.get('username')
        if username and self._other_users.filter(username=username).exists():
            raise forms.ValidationError(
                'This username is already taken.',
                code='unique',
            )
        return username

    def clean_email(self):
        """
        Check that the email address is unique.
        """
        email = self.cleaned_data.get('email')
        if email and self._other_users.filter(email=email).exists():
            raise forms.ValidationError(
                'This email address is already registered.',
                code='unique',
            )
        return email

    def clean_password(self):
        """
        Check password strength.
        """
        password = self.cleaned_data.get('password')
        if password:
            if password_strength(password)['score'] < 2:
                raise forms.ValidationError(
                    ('Please use a stronger password: avoid common patterns and '
                     'make it long enough to be difficult to crack.'),
                    code='invalid',
                )
        elif not (self.instance and self.instance.pk):
            raise forms.ValidationError(
                'Please provide a password.',
                code='required',
            )
        return password

    def clean_password_confirmation(self):
        """
        Check that the password confirmation field matches the password field.
        """
        password = self.cleaned_data.get('password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if password and password_confirmation and password != password_confirmation:
            raise forms.ValidationError(
                "The two password fields didn't match.",
                code='password_mismatch',
            )
        return password

    def clean(self):
        """
        Only allow certain fields to be updated once the application has been
        submitted.
        """
        cleaned_data = super().clean()
        if self.instance and self.instance.pk:
            return {field: value for field, value in cleaned_data.items()
                    if field in self.can_be_modified}
        return cleaned_data

    def save(self, commit=True):
        """
        Create or update User, UserProfile, and BetaTestApplication instances
        with data from the form.
        """
        application = super().save(commit=False)
        if application.pk:
            self.update_related(application, commit=commit)
        else:
            self.create_related(application, commit=commit)
        return application

    def create_related(self, application, commit=True):
        """
        Create related User and UserProfile instance for the given
        BetaTestApplication.
        """
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            is_active=False,
        )
        user.set_password(self.cleaned_data['password'])
        profile = UserProfile(
            full_name=self.cleaned_data['full_name'],
        )
        if commit:
            with transaction.atomic():
                user.save()
                profile.user_id = user.pk
                application.user_id = user.pk
                profile.save()
                application.save()

    def update_related(self, application, commit=True):
        """
        Updated the UserProfile for the given application's user.
        """
        application.user.profile.full_name = self.cleaned_data['full_name']
        if commit:
            with transaction.atomic():
                application.user.profile.save()
                application.save()

    @property
    def _other_users(self):
        """
        Return a queryset for all users that are not the current user, if any.
        """
        users = User.objects.all() #pylint: disable=no-member
        if self.instance and self.instance.user_id:
            users = users.exclude(pk=self.instance.user_id)
        return users


class LoginForm(NgFormValidationMixin, AuthenticationForm,
                metaclass=NgDeclarativeFieldsMetaclass):
    """
    Allows users to login with username/email and password.
    """
    username = forms.CharField(
        label='Your email or username',
        help_text='You can enter either your username or your email to login.',
    )
    password = forms.CharField(
        help_text=('If you have forgotten your login details or need to reset '
                   'your password, please '
                   '<a href="mailto:contact@opencraft.com">contact us</a>.'),
        strip=False,
        widget=forms.PasswordInput,
    )

    def confirm_login_allowed(self, user):
        """
        The default AuthenticationForm rejects inactive users. We would like to
        allow users that have registered but have not yet been approved to log
        in, so we override this method to make it a noop.
        """

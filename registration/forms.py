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
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.text import capfirst
from django.template.loader import get_template
from djng.forms import NgDeclarativeFieldsMetaclass, NgFormValidationMixin, NgModelForm, NgModelFormMixin

from registration.models import BetaTestApplication
from userprofile.models import UserProfile

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

# TODO redo this form (see BIZ-671).
# Use this signature to test:
# class BetaTestApplicationForm(forms.ModelForm):
class BetaTestApplicationForm(NgModelFormMixin, NgFormValidationMixin, NgModelForm):
    """
    Application form for beta testers. Creates instances of User, UserProfile,
    and BetaTestApplication models on submit.
    """
    class Meta:
        model = BetaTestApplication
        exclude = ('user', 'status', 'instance', 'accepted_privacy_policy')
        widgets = {
            'instance_name': TextInput,
            'public_contact_email': EmailInput,
            'project_description': Textarea,
            'privacy_policy_url': URLInput,
            'main_color': TextInput(attrs={'type': 'color'}),
            'link_color': TextInput(attrs={'type': 'color'}),
            'header_bg_color': TextInput(attrs={'type': 'color'}),
            'footer_bg_color': TextInput(attrs={'type': 'color'}),
        }

    # Fields that can be modified after the application has been submitted
    can_be_modified = {
        'full_name',
        'subscribe_to_updates',
        'main_color',
        'link_color',
        'header_bg_color',
        'footer_bg_color',
        'logo',
        'favicon',
        'privacy_policy_url',
    }

    # Fields that when modified need a restart of the instance
    needs_restart = {
        'main_color',
        'link_color',
        'header_bg_color',
        'footer_bg_color',
        'logo',
        'favicon',
    }

    full_name = forms.CharField(
        max_length=255,
        widget=TextInput,
        label='Your full name',
        help_text='Example: Albus Dumbledore',
    )
    username = forms.RegexField(
        regex=r'^[\w.+-]+$',
        max_length=30,
        widget=TextInput,
        help_text=('This would also be the username of the administrator '
                   'account on the Open edX instance.'),
        error_messages={
            'invalid': ('Usernames may contain only letters, numbers, and '
                        './+/-/_ characters.'),
            'unique': 'This username is already taken.',
        },
    )
    email = forms.EmailField(
        widget=EmailInput,
        help_text=('This is also your account name, and where we will send '
                   'important notices.'),
    )
    password_strength = forms.IntegerField(
        widget=forms.HiddenInput,
    )
    password = forms.CharField(
        strip=False,
        widget=PasswordInput,
        help_text=('Pick a password for your OpenCraft account. You will be '
                   'able to use it to login and access your account.'),
    )
    password_confirmation = forms.CharField(
        strip=False,
        widget=PasswordInput,
        help_text=('Please use a strong password: avoid common patterns and '
                   'make it long enough to be difficult to crack.'),
    )
    accept_terms = forms.BooleanField(
        required=True,
        help_text=('I accept that this is a free trial, '
                   'and that the instance is provided without any guarantee.'),
        error_messages={
            'required': 'You must accept these terms to register.',
        },
    )
    accept_privacy_policy = forms.BooleanField(
        required=True,
        help_text=('I accept the privacy policy.'),
        error_messages={
            'required': 'You must accept the privacy policy to register.',
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
        widget=TextInput(attrs={
            'class': 'input input--host input--host--subdomain text-xs-right',
        }),
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
        # Save the request to be able to store notification messages later.
        # AJAX API calls for validation don't pass 'request'.
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

        if self.instance:
            if hasattr(self.instance, 'user'):
                # Populate the username and email fields and make them read only
                for field in ('username', 'email'):
                    self.initial[field] = getattr(self.instance.user, field)
                    self.fields[field].widget.attrs['readonly'] = True

                # Remove the password fields, the user already has a password
                del self.fields['password']
                del self.fields['password_strength']
                del self.fields['password_confirmation']

                # If the user has a profile, populate the full_name field
                if hasattr(self.instance.user, 'profile'):
                    self.initial['full_name'] = self.instance.user.profile.full_name

            if self.instance.pk:
                # If the user has already registered they have already accepted
                # the terms, so the checkbox can default to checked
                self.initial['accept_terms'] = True
                self.fields['accept_terms'].widget.attrs['checked'] = 'checked'
                self.initial['accept_privacy_policy'] = bool(
                    self.instance.accepted_privacy_policy
                )
                self.fields['accept_privacy_policy'].widget.attrs['checked'] = 'checked'

                # Make all non-modifiable fields read only
                for name, field in self.fields.items():
                    if name not in self.can_be_modified:
                        field.widget.attrs['readonly'] = True
            else:
                self.initial['privacy_policy_url'] = settings.DEFAULT_PRIVACY_POLICY_URL

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

    def clean_password_strength(self):
        """
        Check that client submitted password strength, and that value is in expected range.

        If there are issues, produce appropriate warnings but don't raise ValidationError
        (we don't want to display validation errors for this field to users).
        """
        password_strength = self.cleaned_data.get('password_strength')
        if password_strength is None:
            logger.warning('Did not receive password strength from client.')
        elif password_strength not in range(5):
            logger.warning(
                'Received suspicious value for password strength. '
                'Value should be in range [0, 4]. Observed value: {password_strength}',
                **{'password_strength': password_strength}
            )
            password_strength = None
        return password_strength

    def clean_password(self):
        """
        Using score computed on the client, check that password is reasonably strong.
        """
        password = self.cleaned_data.get('password')
        password_strength = self.cleaned_data.get('password_strength')
        if password and password_strength is not None and password_strength < 2:
            raise forms.ValidationError(
                ('Please use a stronger password: avoid common patterns and '
                 'make it long enough to be difficult to crack.'),
                code='invalid',
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

    def restart_fields_changed(self):
        """
        Return true if any of the fields that need a restart were changed
        """
        return any(field in self.changed_data for field in self.needs_restart)

    def save(self, commit=True):
        """
        Create or update User, UserProfile, and BetaTestApplication instances
        with data from the form.
        """
        application = super().save(commit=False)
        application.accepted_privacy_policy = timezone.now()
        if hasattr(application, 'user'):
            self.update_user(application, commit=commit)
        else:
            self.create_user(application, commit=commit)
        return application

    def create_user(self, application, commit=True):
        """
        Create related User and UserProfile instance for the given
        BetaTestApplication.
        """
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
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

    def update_user(self, application, commit=True):
        """
        Update the UserProfile for the given application's user.
        Also detect changes in design fields, store them in instance, and notify us by e-mail.
        """
        if hasattr(application.user, 'profile'):
            application.user.profile.full_name = self.cleaned_data['full_name']
        else:
            application.user.profile = UserProfile(
                full_name=self.cleaned_data['full_name'],
                user_id=application.user.pk,
            )
        if commit:
            with transaction.atomic():
                application.user.profile.save()
                application.save()

        if self.restart_fields_changed():
            messages.add_message(self.request, messages.INFO,
                                 "Thank you for submitting these changes - we will rebuild your instance to "
                                 "apply them, and email you to confirm once it is up to date.")

            # Notify us
            if settings.VARIABLES_NOTIFICATION_EMAIL:
                subject = 'Update required at instance {name}'.format(
                    name=application.subdomain,
                )
                template = get_template('registration/fields_changed_email.txt')
                text = template.render(dict(
                    application=application,
                    changed_fields=self.changed_data,
                ))
                sender = settings.DEFAULT_FROM_EMAIL
                dest = [settings.VARIABLES_NOTIFICATION_EMAIL]
                send_mail(subject, text, sender, dest)

    def fields_with_errors(self):
        """
        Returns a list of fields that did not pass validation, in a
        human-readable format.
        """
        return [self[field].label for field in self.errors]

    @property
    def _other_users(self):
        """
        Return a queryset for all users that are not the current user, if any.
        """
        users = User.objects.all()
        if self.instance and self.instance.user_id:
            users = users.exclude(pk=self.instance.user_id)
        return users


# TODO redo this form (see BIZ-671).
# Use this signature to test:
# class LoginForm(AuthenticationForm):
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

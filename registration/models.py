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
Models for the Instance Manager beta test
"""

# Imports #####################################################################

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.models import TimeStampedModel
from simple_email_confirmation.models import EmailAddress

from instance.models.mixins.domain_names import generate_internal_lms_domain
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.utils import ValidateModelMixin


# Models ######################################################################

def validate_available_subdomain(subdomain):
    """
    Check that the given subdomain is not blacklisted.
    """
    if subdomain in settings.SUBDOMAIN_BLACKLIST:
        raise ValidationError(
            message='This domain name is not publicly available.',
            code='blacklisted',
        )


class BetaTestApplication(ValidateModelMixin, TimeStampedModel):
    """
    An application to beta test the Instance Manager.
    """
    BASE_DOMAIN = 'opencraft.hosting'

    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subdomain = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='domain name',
        help_text=('The URL students will visit. In the future, you will also '
                   'have the possibility to use your own domain name.'
                   '\n\nExample: hogwarts.{0}').format(BASE_DOMAIN),
        validators=[
            validators.MinLengthValidator(
                3,
                'The subdomain name must at least have 3 characters.',
            ),
            validators.RegexValidator(
                r'^[\w.-]+$',
                "Please include only letters, numbers, '_', '-' and '.'",
            ),
            validate_available_subdomain,
        ],
        error_messages={
            'unique': 'This domain is already taken.',
            'blacklisted': 'This domain name is not publicly available.',
        },
    )
    instance_name = models.CharField(
        max_length=255,
        help_text=('The name of your institution, company or project.'
                   '\n\nExample: Hogwarts Online Learning'),
    )
    public_contact_email = models.EmailField(
        help_text=('The email your instance of Open edX will be using to '
                   'send emails, and where your users should send their '
                   'support requests.'
                   '\n\nThis needs to be a valid email.'),
    )
    project_description = models.TextField(
        verbose_name='your project',
        help_text=('What are you going to use the instance for? What are '
                   'your expectations?'),
    )

    # Theme fields. They allow to define the design, e.g. choose colors and logo
    main_color = models.CharField(
        max_length=7,
        help_text='This is used as the primary color in your theme palette.',
        default='#333333', # #333333 == text-color == rgb(51, 51, 51)
    )
    link_color = models.CharField(
        max_length=7,
        help_text='This is used as the color for clickable links on your '
                  'instance.',
        default='#0075b4', # #0075b4 == link-color == rgb(0, 117, 180)

    )
    bg_color_1 = models.CharField(
        max_length=7,
        verbose_name='Primary background color',
        help_text='Used as the main filler color for buttons, background, etc.',
        default='#126f9a', # #126f9a == m-blue-d3 == rgb(18,111,154)
    )
    bg_color_2 = models.CharField(
        max_length=7,
        verbose_name='Secondary background color',
        help_text='Used as the secondary filler color for buttons, background, '
                  'etc.',
        default='#c2387d', # #c2387d == m-pink == rgb(194, 56, 125)
    )
    logo = models.ImageField(
        help_text='Your branding to be displayed throughout your instance.',
        null=True, # to ease migrations
        blank=False,
    )
    favicon = models.ImageField(
        help_text="This is used as the browser tab icon for your instance's "
                  "pages.",
        null=True, # to ease migrations
        blank=False,
    )

    subscribe_to_updates = models.BooleanField(
        default=False,
        help_text=('I want OpenCraft to keep me updated about the progress '
                   'of the beta test, and occasionally send me an email '
                   'about it.'),
    )
    status = models.CharField(
        max_length=255,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    instance = models.ForeignKey(
        OpenEdXInstance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.domain

    @property
    def domain(self):
        """
        The full domain requested for this application.
        """
        return '{0}.{1}'.format(self.subdomain, self.BASE_DOMAIN)

    def email_addresses_verified(self):
        """
        Return True if both the user's email address and this application's
        public contact email address have been verified.
        """
        email_addresses = {self.user.email, self.public_contact_email}
        verified = EmailAddress.objects.exclude(confirmed_at=None).filter(
            email__in=email_addresses
        )
        return verified.count() == len(email_addresses)

    def clean(self):
        """
        Verify that the subdomain has not already been taken by any running instance.

        We can't do this in a regular validator, since we have to allow the subdomain of the
        instance associated with this application.
        """
        generated_domain = generate_internal_lms_domain(self.subdomain)
        if self.instance is not None and self.instance.internal_lms_domain == generated_domain:
            return
        if OpenEdXInstance.objects.filter(internal_lms_domain=generated_domain).exists():
            subdomain_error = ValidationError(
                message='This domain is already taken.',
                code='unique',
            )
            raise ValidationError({'subdomain': [subdomain_error]})

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
Models for the Instance Manager beta test
"""

# Imports #####################################################################

import logging
import tldextract

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django_extensions.db.models import TimeStampedModel
from simple_email_confirmation.models import EmailAddress

from instance.gandi import api as gandi_api
from instance.models.mixins.domain_names import generate_internal_lms_domain, is_subdomain_contains_reserved_word
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.utils import ValidateModelMixin
from instance.schemas.static_content_overrides import static_content_overrides_schema_validate
from instance.schemas.theming import theme_schema_validate
from instance.utils import create_new_deployment, DjangoChoiceEnum

logger = logging.getLogger(__name__)


# Models ######################################################################


def validate_color(color):
    """
    Check the color is either #123 or #123456
    """
    validators.RegexValidator(
        r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        f'{color} is not a valid color, it must be either #123 or #123456',
    )(color)


def validate_available_external_domain(value):
    """
    Prevent users from registering with an external domain which was or currently in use.

    The validation reduces the risk of security issues when someone is trying to take over
    control of a client resource (domain) if they forget to restrict its access.
    """
    default_instance_domain = tldextract.extract(settings.DEFAULT_INSTANCE_BASE_DOMAIN)
    domain_data = tldextract.extract(value)
    domain = domain_data.registered_domain

    if domain in settings.EXTERNAL_DOMAIN_BLACKLIST:
        raise ValidationError(
            message='This domain name is not publicly available.',
            code='blacklisted'
        )

    if default_instance_domain.registered_domain == domain:
        raise ValidationError(
            message=f'The domain "{value}" is not allowed.',
            code='reserved'
        )

    if is_subdomain_contains_reserved_word(value):
        raise ValidationError(
            message=f'Cannot register domain starting with "{domain_data.subdomain}".',
            code='reserved'
        )

    is_domain_used_for_beta_app = BetaTestApplication.objects.filter(
        Q(external_domain=domain)
        | Q(external_domain__endswith=f".{domain}")
    ).exists()

    if is_domain_used_for_beta_app:
        raise ValidationError(
            message='This domain is already taken.',
            code='unique'
        )

    is_taken = OpenEdXInstance.objects.filter(
        Q(external_lms_domain=domain)
        | Q(external_lms_preview_domain__endswith=domain)
        | Q(external_studio_domain__endswith=domain)
        | Q(external_discovery_domain__endswith=domain)
        | Q(external_ecommerce_domain__endswith=domain)
        # No need to check for subdomain, since it will match anyway
        | Q(extra_custom_domains__contains=domain)
    ).exists()

    if is_taken:
        raise ValidationError(
            message='This domain is already taken.',
            code='unique'
        )


def validate_subdomain_is_not_blacklisted(value):
    """
    Validate that a subdomain is not blacklisted.
    """
    if value in settings.SUBDOMAIN_BLACKLIST:
        raise ValidationError(message='This domain name is not publicly available.', code='blacklisted')


def validate_available_subdomain(value):
    """
    Prevent users from registering with a subdomain which is in use.

    The validation reduces the risk of security issues when someone is trying to take over
    control of a client resource (domain) if they forget to restrict its access.
    """
    if is_subdomain_contains_reserved_word(value):
        raise ValidationError(message=f'Cannot register domain starting with "{value}".', code='reserved')

    # if subdomain_exists return instead of raising validation error, because the unique
    # check already raises the error
    generated_domain = generate_internal_lms_domain(value)
    is_subdomain_registered = BetaTestApplication.objects.filter(subdomain=value).exists()
    is_assigned_to_instance = OpenEdXInstance.objects.filter(internal_lms_domain=generated_domain).exists()

    if is_subdomain_registered or is_assigned_to_instance:
        raise ValidationError(message='This domain is already taken.', code='unique')

    managed_domains = set([
        settings.DEFAULT_INSTANCE_BASE_DOMAIN,
        settings.GANDI_DEFAULT_BASE_DOMAIN,
    ])

    for domain in managed_domains:
        try:
            records = gandi_api.filter_dns_records(domain)
            records = {tldextract.extract(record["name"]) for record in records}
        except Exception as exc:
            logger.warning('Unable to retrieve the domains for %s: %s.', domain, str(exc))
            raise ValidationError(message='The domain cannot be validated.', code='cannot_validate')

        # Because registered CNAMEs may have multiple dots (.) in their subdomain
        # we need to check for the starting and ending part of it.
        # Ex: haproxy-integration.my.net.opencraft.hosting is registered, but we must reject
        # registrations for net.opencraft.hosting and haproxy-integration.my.net as well.
        registered_subdomains = set()
        for dns_record in records:
            registered_subdomains.update([
                dns_record.subdomain,  # the whole subdomain
                dns_record.subdomain.split(".")[-1]  # base of the subdomain like .net.*
            ])

        subdomain_base = value.split(".")[-1]
        if value in registered_subdomains or subdomain_base in registered_subdomains:
            raise ValidationError(message='This domain is already taken.', code='unique')


def validate_logo_height(image):
    """
    Validates that the logo is 48px tall (otherwise it would require extra CSS).
    """

    if image.name == 'opencraft_logo_small.png':
        # Don't check the default image (which is in SWIFT). This gives more flexibility in
        # dev (we don't need to set up the right images in the every SWIFT container). Could
        # be made safer.
        return

    if image.height != 48:
        raise ValidationError("The logo image must be 48px tall to fit into the header.")


class DNSConfigState(DjangoChoiceEnum):
    """
    Enumeration for states of DNS Config Verification
    """
    verified = 'External domain DNS configured'
    pending = 'External domain config verification pending'
    failed = 'External domain DNS not configured'
    not_required = 'No external domain set'


class BetaTestApplication(ValidateModelMixin, TimeStampedModel):
    """
    An application to beta test the Instance Manager.
    """
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
                   '\n\nExample: hogwarts.opencraft.hosting'),
        validators=[
            validators.MinLengthValidator(
                3,
                'The subdomain name must at least have 3 characters.',
            ),
            validators.MaxLengthValidator(
                63,
                'The subdomain name can have at most have 63 characters.',
            ),
            validators.RegexValidator(
                r'^[a-z0-9]([a-z0-9\-]+[a-z0-9])?$',
                'Please choose a name of at least 3 characters, using '
                'lower-case letters, numbers, and hyphens. '
                'Cannot start or end with a hyphen.',
            ),
            validate_subdomain_is_not_blacklisted,
        ],
        error_messages={
            'unique': 'This domain is already taken.',
            'blacklisted': 'This domain name is not publicly available.',
            'reserved': 'Cannot register domain with this subdomain.',
            'cannot_validate': 'The domain cannot be validated.'
        },
    )
    external_domain = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='external domain name',
        blank=True,
        null=True,
        help_text=(
            'The URL students will visit if you are using an external domain.'
        ),
        validators=[
            validators.MinLengthValidator(
                3,
                'The subdomain name must at least have 3 characters.',
            ),
            validators.MaxLengthValidator(
                250,
                'The subdomain name can have at most have 250 characters.',
            ),
            validators.RegexValidator(
                r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$',
                'Please choose a domain name that you already know and own, '
                'containing lower-case letters, numbers, dots, and hyphens. '
                'Cannot start or end with a hyphen.',
            ),
            validate_subdomain_is_not_blacklisted,
        ],
        error_messages={
            'unique': 'This domain is already taken.',
            'blacklisted': 'This domain name is not publicly available.',
            'reserved': 'Cannot register domain with this subdomain.',
        },
    )
    dns_configuration_state = models.CharField(
        max_length=15,
        choices=DNSConfigState.choices(),
        default=DNSConfigState.not_required,
        help_text=('State of DNS config verfication for external_domain')
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
        blank=True, default=''
    )
    privacy_policy_url = models.URLField(
        verbose_name='URL to Privacy Policy',
        help_text=('URL to the privacy policy.'),
        blank=True,
        default='',
    )

    # Theme fields. They allow to define the design, e.g. choose colors and logo
    main_color = models.CharField(
        max_length=7,
        help_text='This is used as the primary color in your theme palette. '
                  'It is used as filler for buttons.',
        # #126f9a == $m-blue-d3 in variables.scss. It's rgb(18,111,154)
        default='#126f9a',
        validators=[validate_color],
    )
    link_color = models.CharField(
        max_length=7,
        help_text='This is used as the color for clickable links on your '
                  'instance.',
        # Same as main_color. Almost like openedx's #0075b4 == rgb(0, 117, 180)
        default='#126f9a',
        validators=[validate_color],
    )
    header_bg_color = models.CharField(
        max_length=7,
        verbose_name='Header background color',
        help_text='Used as the background color for the top bar.',
        # openedx also uses white by default
        default='#ffffff',
        validators=[validate_color],
    )
    footer_bg_color = models.CharField(
        max_length=7,
        verbose_name='Footer background color',
        help_text='Used as the background color for the footer.',
        # openedx also uses white by default
        default='#ffffff',
        validators=[validate_color],
    )

    footer_logo_image = models.ImageField(
        verbose_name='Footer Logo Image',
        help_text="If set, it overrides the source for the footer logo image."
                  " By default, the 'Powered by OpenEdX' logo is used.",
        blank=True,
        default='',
        null=True,
    )
    footer_logo_url = models.URLField(
        verbose_name='Footer Logo Link',
        help_text="If set, overrides the link destination for the footer logo."
                  " By default, it links to the OpenEdX website.",
        blank=True,
        default=''
    )
    # If you're using SWIFT (OpenStack) to store files (this is enabled through
    # the MEDIAFILES_SWIFT_ENABLE environment variable) then you'll need to
    # upload these default images (logo and favicon) to your container. To do so,
    # download the configuration file from the OVH account (top right menu), and
    # run (replacing the cointainer name):
    #
    # source downloaded_openstack_configuration_file.sh
    # swift stat  # this is only to test the connection
    # swift upload 'daniel_testing_file_uploads_from_ocim' \
    #   static/img/png/opencraft_logo_small.png            \
    #   --object-name opencraft_logo_small.png
    # swift upload 'daniel_testing_file_uploads_from_ocim' \
    #   static/img/favicon/opencraft_favicon.ico           \
    #   --object-name opencraft_favicon.ico
    # swift list daniel_testing_file_uploads_from_ocim  # just to check
    #
    # Note that the file names must match the names used in "default", and that
    # the logo should be 48px tall.
    logo = models.ImageField(
        help_text="Your branding to be displayed throughout your instance. "
                  "It should be 48px tall. "
                  "If unset, OpenCraft's logo will be used.",
        null=True,  # to ease migrations
        blank=False,
        default='opencraft_logo_small.png',
        validators=[validate_logo_height],
    )
    # Same upload instructions as logo
    favicon = models.ImageField(
        help_text="This is used as the browser tab icon for your instance's "
                  "pages. If unset, OpenCraft's icon will be used.",
        null=True,  # to ease migrations
        blank=False,
        default='opencraft_favicon.ico',
    )
    hero_cover_image = models.ImageField(
        help_text="This is used as the cover image for the hero section in the instance LMS home page.",
        null=True,  # to ease migrations
        blank=True,
        default=None
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
    use_advanced_theme = models.BooleanField(
        default=False,
        help_text=('The advanced theme allows users to pick a lot more details than the regular theme.'
                   'Setting this flag will enable the more complex theme editor.'),
    )
    draft_theme_config = JSONField(
        verbose_name='Draft Theme Configuration JSON',
        validators=[theme_schema_validate],
        null=True,
        blank=True,
        help_text=('The theme configuration data currently being edited by the user. When finalised it will'
                   'be copied over to the final theme config which will then be deployed to the next appserver'
                   'that is launched.'),
    )

    draft_static_content_overrides = JSONField(
        verbose_name='Draft static content overrides JSON',
        validators=[static_content_overrides_schema_validate],
        null=True,
        blank=True,
        default=None,
        help_text=("The static content overrides data currently being edited by the user. When finalised, it will "
                   'be copied over to the final static content overrides which will then be deployed to the '
                   'next appserver that is launched')
    )
    configuration_display_static_pages = JSONField(  # pylint:disable=invalid-name
        blank=True,
        null=True,
        default=None,
        help_text="Configure `MKTG_URL_LINK_MAP` to display/hide static pages",
    )

    def __str__(self):
        return self.domain

    @property
    def first_activated(self):
        """
        Return the activation date for the first AppServer to activate.
        """
        if self.instance:
            return self.instance.first_activated
        return None

    @property
    def domain(self):
        """
        The full domain requested for this application.
        """
        return f'{self.subdomain}.{settings.DEFAULT_INSTANCE_BASE_DOMAIN}'

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
        Verify that the domains were not already been taken by any running instance.

        We can't do this in a regular validator, since we have to allow the subdomain of the
        instance associated with this application.
        """
        errors = {}

        original_data = next(iter(BetaTestApplication.objects.filter(pk=self.pk)), None)
        is_subdomain_updated = original_data and original_data.subdomain != self.subdomain
        is_external_domain_updated = original_data and original_data.external_domain != self.external_domain

        # Check internal domain
        generated_domain = generate_internal_lms_domain(self.subdomain)
        if self.instance is not None and self.instance.internal_lms_domain == generated_domain:
            return

        if is_subdomain_updated:
            validate_available_subdomain(self.subdomain)

        if OpenEdXInstance.objects.filter(internal_lms_domain=generated_domain).exists():
            subdomain_error = ValidationError(
                message='This domain is already taken.',
                code='unique',
            )
            errors['subdomain'] = [subdomain_error]

        # Check external domain, if present
        if self.external_domain:
            if self.instance is not None and self.instance.external_lms_domain == self.external_domain:
                return

            if is_external_domain_updated:
                validate_available_external_domain(self.external_domain)

            if OpenEdXInstance.objects.filter(external_lms_domain=self.external_domain).exists():
                external_domain_error = ValidationError(
                    message='This domain is already taken.',
                    code='unique',
                )
                errors['external_domain'] = [external_domain_error]

        if errors:
            raise ValidationError(errors)

    def default_configuration_display_static_pages(self):
        """
        All static pages enabled by default
        """
        return {
            "about": True,
            "contact": True,
            "donate": True,
            "tos": True,
            "honor": True,
            "privacy": True,
        }

    def get_disabled_mktg_links(self):
        """
        Get disabled MKTG links.
        """
        result = []
        if self.configuration_display_static_pages:
            for page_name, enabled in self.configuration_display_static_pages.items():
                if not enabled:
                    result.append(page_name)
            return {page_name: None for page_name in result}
        return {}

    def commit_changes_to_instance(
            self,
            deploy_on_commit=False,
            retry_attempts=2,
            creator=None,
            deployment_type=None,
            cancel_pending_deployments=False
    ):
        """
        Copies over configuration changes stored in this model to the related instance,
        and optionally spawn a new instance.

        :param deploy_on_commit: Initiate new deployment after committing changes
        :param deployment_type: Type of deployment
        :param creator: User initiating deployment
        :param retry_attempts: Number of times to retry deployment
        """
        instance = self.instance
        if instance is None:
            return

        instance.theme_config = self.draft_theme_config
        instance.static_content_overrides = self.draft_static_content_overrides
        instance.static_content_display = self.get_disabled_mktg_links()
        instance.name = self.instance_name
        instance.privacy_policy_url = self.privacy_policy_url
        instance.email = self.public_contact_email
        instance.save()
        if deploy_on_commit:
            create_new_deployment(
                instance,
                creator=creator,
                deployment_type=deployment_type,
                mark_active_on_success=True,
                num_attempts=retry_attempts,
                cancel_pending=cancel_pending_deployments,
                add_delay=True,
            )

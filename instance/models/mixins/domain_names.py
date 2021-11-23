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
Instance app model mixins - domain names
"""
import re

from django.db import models
from django.conf import settings
from django.utils.text import slugify

# Constants ###################################################################

DOMAIN_PREFIXES = [
    'studio',
    'preview',
    'discovery',
    'ecommerce',
    'app'
]

# Functions ###################################################################


def is_subdomain_contains_reserved_word(subdomain: str) -> bool:
    """
    Check if the subdomain contains a reserved word.
    """
    return subdomain.split('.')[0] in DOMAIN_PREFIXES


def generate_internal_lms_domain(sub_domain):
    """
    Generates value for internal_lms_domain field from the supplied sub_domain and the
    DEFAULT_INSTANCE_BASE_DOMAIN setting.
    """
    return '{}.{}'.format(sub_domain, settings.DEFAULT_INSTANCE_BASE_DOMAIN)


# Classes #####################################################################

class DomainNameInstance(models.Model):
    """
    Mixin stores and provides logic around the retrieval of domain names and
    domain name-based information.
    """
    domain_hierarchy = [
        "external",
        "internal",
    ]

    allowed_domain_attributes = {
        'domain': 'lms',
        'lms_preview_domain': 'lms_preview',
        'studio_domain': 'studio',
        'ecommerce_domain': 'ecommerce',
        'discovery_domain': 'discovery',
        'mfe_domain': 'app'
    }

    nginx_domain_regex_attributes = {
        'studio_domain_nginx_regex': 'studio',
        'discovery_domain_nginx_regex': 'discovery',
        'ecommerce_domain_nginx_regex': 'ecommerce',
        'mfe_domain_nginx_regex': 'app'
    }

    domain_attr_template = '{domain_type}_{domain_key}_domain'

    # Internal domains are controlled by us and their DNS records are automatically set to point to the current active
    # appserver. They are generated from a unique prefix (given as 'sub_domain' in instance factories) and the value of
    # DEFAULT_INSTANCE_BASE_DOMAIN at instance creation time. They cannot be blank and are normally never changed after
    # the instance is created.
    # External domains on the other hand are controlled by the customer and are optional. We use external domains in
    # preference to internal domains when displaying links to the instance in the UI and when passing domain-related
    # settings to Ansible vars when provisioning appservers.
    # The `domain`, `lms_preview_domain`, and `studio_domain` properties below are useful if you need to access
    # corresponding domains regardless of whether an instance uses external domains or not (they return the external
    # domain if set, and fall back to the corresponding internal domain otherwise).
    internal_lms_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_lms_preview_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_studio_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_discovery_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_ecommerce_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_mfe_domain = models.CharField(max_length=100, blank=False, unique=True)

    external_lms_domain = models.CharField(max_length=100, blank=True)
    external_lms_preview_domain = models.CharField(max_length=100, blank=True)
    external_studio_domain = models.CharField(max_length=100, blank=True)
    external_discovery_domain = models.CharField(max_length=100, blank=True)
    external_ecommerce_domain = models.CharField(max_length=100, blank=True)
    external_mfe_domain = models.CharField(max_length=100, blank=True)
    extra_custom_domains = models.TextField(default='', blank=True, help_text=(
        "Add custom domain names, one per line. Domain names must be sub domains of the main LMS domain."
    ))

    enable_prefix_domains_redirect = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        """
        OpenEdXInstance constructor.

        The constructor is overridden to optionally accept a 'sub_domain' parameter instead of a full
        value for 'internal_lms_domain'. When 'sub_domain' is provided, the 'internal_lms_domain' field is automatically
        generated from from the value of 'sub_domain' and the DEFAULT_INSTANCE_BASE_DOMAIN setting.
        """
        if 'sub_domain' in kwargs:
            sub_domain = kwargs.pop('sub_domain')
            if 'internal_lms_domain' not in kwargs:
                kwargs['internal_lms_domain'] = generate_internal_lms_domain(sub_domain)
        super().__init__(*args, **kwargs)

    def __getattr__(self, domain_attr):
        """
        Catches missing attribute calls, checks if they're lookups for
        supported domain names, and if so, find and return the correct
        domain name, choosing between internal domain and external
        domain (if that variable has been set for this instance).
        """
        domain_key = self.allowed_domain_attributes.get(domain_attr)
        nginx_regex_key = self.nginx_domain_regex_attributes.get(domain_attr)
        if domain_key is not None:
            return self.get_domain(domain_key)
        if nginx_regex_key is not None:
            return self.domain_nginx_regex(nginx_regex_key)
        return super().__getattribute__(domain_attr)

    def get_domain(self, domain_key):
        """
        Returns the external domain for the given site if present; otherwise,
        falls back to the internal domain.
        """
        for domain_type in self.domain_hierarchy:
            domain_attr = self.domain_attr_template.format(
                domain_type=domain_type,
                domain_key=domain_key
            )
            domain_name = getattr(self, domain_attr, None)
            if domain_name:
                return domain_name
        return None

    def domain_nginx_regex(self, site_name):
        """
        Regex that matches either the internal or external URL for the site.

        This is meant exclusively for filling in the server_name regex in nginx configs.
        """
        domains = []
        for domain_type in self.domain_hierarchy:
            domain = getattr(
                self,
                self.domain_attr_template.format(
                    domain_type=domain_type,
                    domain_key=site_name
                ),
                None,
            )
            if domain:
                domains.append(domain)
        choices = '|'.join([re.escape(x) for x in domains])
        return '^({})$'.format(choices)

    def get_prefix_domain_names(self):
        """
        Return an iterable of domain names using prefixes for Studio, Preview, Discovery, E-Commerce, MFEs
        """
        return ['{}-{}'.format(prefix, self.internal_lms_domain) for prefix in DOMAIN_PREFIXES]

    def get_load_balanced_domains(self):
        """
        Return an iterable of domains that should be handled by the load balancer.
        """
        domain_names = [
            self.external_lms_domain,
            self.external_lms_preview_domain,
            self.external_studio_domain,
            self.external_discovery_domain,
            self.external_ecommerce_domain,
            self.external_mfe_domain,
            self.internal_lms_domain,
            self.internal_lms_preview_domain,
            self.internal_studio_domain,
            self.internal_discovery_domain,
            self.internal_ecommerce_domain,
            self.internal_mfe_domain,
        ] + self.extra_custom_domains.splitlines()
        return [name for name in domain_names if name]

    def get_managed_domains(self):
        """
        Return an iterable of domains that we manage DNS entries for.
        """
        managed_domains = [
            self.internal_lms_domain,
            self.internal_lms_preview_domain,
            self.internal_studio_domain,
            self.internal_discovery_domain,
            self.internal_ecommerce_domain,
            self.internal_mfe_domain,
        ]
        if self.enable_prefix_domains_redirect:
            managed_domains += self.get_prefix_domain_names()

        # Filter out external custom domains here, because we can only manage
        # DNS entries for internal domains.
        managed_domains += [
            domain for domain in self.extra_custom_domains.splitlines() if domain.endswith(self.internal_lms_domain)
        ]
        return [name for name in managed_domains if name]

    @property
    def domain_slug(self):
        """
        Returns a slug-friendly name for this instance, using the domain name.
        """
        prefix = ('edxins-' + slugify(self.domain))[:20]
        return "{prefix}-{num}".format(prefix=prefix, num=self.id)

    @property
    def url(self):
        """
        LMS URL.
        """
        return u'https://{}/'.format(self.domain)

    @property
    def studio_url(self):
        """
        Studio URL.
        """
        return u'https://{}/'.format(self.studio_domain)

    @property
    def lms_preview_url(self):
        """
        LMS preview URL.
        """
        return u'https://{}/'.format(self.lms_preview_domain)

    @property
    def lms_extended_heartbeat_url(self):
        """
        LMS extended heartbeat URL.
        """
        return u'{}heartbeat?extended'.format(self.url)

    def save(self, **kwargs):  # pylint: disable=arguments-differ, too-many-branches, useless-suppression; # noqa: MC0001
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.internal_lms_preview_domain:
            self.internal_lms_preview_domain = settings.DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX + self.internal_lms_domain
        if not self.internal_studio_domain:
            self.internal_studio_domain = settings.DEFAULT_STUDIO_DOMAIN_PREFIX + self.internal_lms_domain
        if not self.internal_discovery_domain:
            self.internal_discovery_domain = settings.DEFAULT_DISCOVERY_DOMAIN_PREFIX + self.internal_lms_domain
        if not self.internal_ecommerce_domain:
            self.internal_ecommerce_domain = settings.DEFAULT_ECOMMERCE_DOMAIN_PREFIX + self.internal_lms_domain
        if not self.internal_mfe_domain:
            self.internal_mfe_domain = settings.DEFAULT_MFE_DOMAIN_PREFIX + self.internal_lms_domain

        # Save for external domain, but only when present
        if self.external_lms_domain:
            if not self.external_lms_preview_domain:
                self.external_lms_preview_domain = settings.DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX + self.external_lms_domain
            if not self.external_studio_domain:
                self.external_studio_domain = settings.DEFAULT_STUDIO_DOMAIN_PREFIX + self.external_lms_domain
            if not self.external_discovery_domain:
                self.external_discovery_domain = settings.DEFAULT_DISCOVERY_DOMAIN_PREFIX + self.external_lms_domain
            if not self.external_ecommerce_domain:
                self.external_ecommerce_domain = settings.DEFAULT_ECOMMERCE_DOMAIN_PREFIX + self.external_lms_domain
            if not self.external_mfe_domain:
                self.external_mfe_domain = settings.DEFAULT_MFE_DOMAIN_PREFIX + self.external_lms_domain

        super().save(**kwargs)

# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Views for Community Resources
"""

# Imports #####################################################################

from collections import defaultdict

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import loader

from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.mixins.secret_keys import OPENEDX_SECRET_KEYS, OPENEDX_SHARED_KEYS, generate_secret_key


# Utils #######################################################################

class ForcedDefaultDict(defaultdict):
    """
    A defaultdict that always returns True for __contains__
    This is required to use a defaultdict as the root context dict
    when rendering a django template.
    """
    def __contains__(self, key):
        """ is key in this defaultdict? """
        return True


# Views #######################################################################

def example_openstack_vars(_request):
    """
    Output some example ansible variables that contain no secrets

    We cannot use the actual code from
    OpenEdXAppServer.create_configuration_settings
    because we can't control its context and it could easily contain
    secrets from django settings, etc.

    To keep this secure, we must render the templates here, with full
    control over the template context.
    """
    context = ForcedDefaultDict(
        lambda: 'SET ME',
        appserver=defaultdict(
            lambda: 'SET ME',
            github_admin_username_list=['"SET ME to a GitHub username to grant that user SSH access"'],
        ),
        instance=defaultdict(
            lambda: 'SET ME',
            domain='www.example.com',
            lms_preview_domain='preview.example.com',
            studio_domain='studio.example.com',
            studio_domain_nginx_regex='studio.example.com',
        ),
        smtp_relay_settings=defaultdict(
            lambda: 'SET ME',
            port='25',
            rewritten_address=None,  # Exclude the vars for rewriting 'From' addresses
        ),
        newrelic_license_key='',
    )

    templates = [
        OpenEdXAppServer.CONFIGURATION_VARS_TEMPLATE,
        'instance/ansible/mysql.yml',
        'instance/ansible/mongo.yml',
        'instance/ansible/rabbitmq.yml',
        'instance/ansible/swift.yml',
    ]

    vars_out = '\n\n'.join(
        loader.get_template(template).render(context)
        for template in templates
    )

    # Add the secret keys
    vars_out += '\n\n## Secret keys (examples are random but you should change them):\n'
    for secret_name in OPENEDX_SECRET_KEYS:
        secret_value = generate_secret_key(40).decode('utf-8')
        vars_out += '{}: "{}"\n'.format(secret_name, secret_value)
    for secret_name, source_key_name in OPENEDX_SHARED_KEYS.items():
        vars_out += secret_name + ': "{{ ' + source_key_name + ' }}"\n'

    vars_out += '\n'


    return HttpResponse(
        "<html><body>"
        "<h1>OpenCraft's Example OpenStack vars for Open edX</h1><br>"
        "<pre>{}</pre>"
        "</body></html>"
        .format(vars_out)
    )

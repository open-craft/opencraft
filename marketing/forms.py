# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <xavier@opencraft.com>
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
Forms for the `marketing` app
"""
from decimal import Decimal

from django.contrib.postgres.forms.jsonb import JSONField
from django.forms import DecimalField, Form, ModelChoiceField, ValidationError

from instance.models.openedx_instance import OpenEdXInstance


class CustomInstanceChoiceField(ModelChoiceField):
    """
    Custom ModelChoiceField to customize the label to show for the instances in the queryset.
    """
    def label_from_instance(self, obj):
        """
        Customize the label used for the instance objects.
        """
        instance_name = obj.ref.name if obj.ref.name else '<Unset>'
        instance_creator = obj.creator_username if obj.creator_username else '<Unknown user>'
        return f'{obj.domain} - {instance_name} - {instance_creator}'


class ConversionForm(Form):
    """
    Form to handle and validate the conversion data to be sent to Matomo.
    """
    instance = CustomInstanceChoiceField(
        queryset=OpenEdXInstance.objects.filter(
            betatestapplication__isnull=False,
            ref_set__is_archived=False,
            successfully_provisioned=True
        ),
        help_text='Select the instance to enter the conversion data for.'
    )
    revenue = DecimalField(
        min_value=Decimal('0.00'),
        decimal_places=2,
        help_text='Revenue per month ($) from this instance.'
    )
    custom_matomo_tracking_data = JSONField(
        initial=dict,
        required=False,
        help_text='A JSON object containing any additional custom Matomo tracking data.',
        error_messages={'invalid': 'The value must be a valid JSON object.'},
    )

    def clean_custom_matomo_tracking_data(self):
        """
        Validate whether the value is a JSON object or not.
        """
        custom_matomo_tracking_data = self.cleaned_data['custom_matomo_tracking_data']
        if not isinstance(custom_matomo_tracking_data, dict):
            raise ValidationError(
                'The value must be a valid JSON object.'
            )
        return custom_matomo_tracking_data

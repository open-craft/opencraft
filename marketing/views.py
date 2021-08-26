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
Views for the `marketing` app
"""
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from .forms import ConversionForm


logger = logging.getLogger(__name__)

decorators = [login_required, user_passes_test(lambda u: u.is_superuser)]


@method_decorator(decorators, name='dispatch')
class ConversionView(FormView):
    """
    View to handle conversion data submission to Matomo.
    """
    form_class = ConversionForm
    template_name = 'marketing/conversion.html'
    success_url = reverse_lazy('marketing:conversion')

    def form_valid(self, form):
        """
        Contains the actions to perform when the form is valid.
        """
        revenue = form.cleaned_data['revenue'].quantize(Decimal('0.01'))

        payload = {
            'idsite': settings.MATOMO_SITE_ID,
            'url': self.request.META['HTTP_HOST'] + self.get_success_url(),
            'uid': form.cleaned_data['instance'].creator_username,
            'e_c': 'conversion',
            'e_a': 'paid-first-invoice',
            'e_v': revenue,
            'idgoal': settings.MATOMO_CONVERSION_GOAL_ID,
            'revenue': revenue,
            'new_visit': 1,
            'rec': 1,
        }

        custom_matomo_tracking_data = form.cleaned_data['custom_matomo_tracking_data']
        if custom_matomo_tracking_data and isinstance(custom_matomo_tracking_data, dict):
            payload.update(form.cleaned_data['custom_matomo_tracking_data'])

        try:
            response = requests.get(settings.MATOMO_URL + '/matomo.php', params=payload)
            response.raise_for_status()

            logger.info('Conversion data sent to Matomo successfully for %s.', form.cleaned_data['instance'].domain)
            messages.success(self.request, 'Conversion data sent to Matomo successfully.')
        except Exception:  # pylint: disable=broad-except
            logger.exception('Error sending conversion data to Matomo for %s.', form.cleaned_data['instance'].domain)
            messages.error(self.request, 'Error sending conversion data to Matomo.', extra_tags='alert')

        return HttpResponseRedirect(self.get_success_url())

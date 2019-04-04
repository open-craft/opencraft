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
Registration views
"""

# Imports #####################################################################

from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import UpdateView
from simple_email_confirmation.models import EmailAddress

from email_verification import send_email_verification
from registration.forms import BetaTestApplicationForm
from registration.models import BetaTestApplication


# Views #######################################################################

class BetaTestApplicationMixin:
    """
    Mix this in to generic views to provide a beta test application for the
    logged in user.
    """
    def get_object(self, *args, **kwargs):
        """
        Get the beta test application for the logged in user, if any.
        """
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'betatestapplication'):
                return self.request.user.betatestapplication
            application = BetaTestApplication()
            application.user = self.request.user
            return application
        return None


@method_decorator(
    sensitive_post_parameters('password', 'password_confirmation'), name='post'
)
class BetaTestApplicationView(BetaTestApplicationMixin, UpdateView):
    """
    Display the beta test application form.
    """
    template_name = 'registration/registration.html'
    form_class = BetaTestApplicationForm
    success_url = reverse_lazy('registration:register')

    @transaction.atomic
    def form_valid(self, form):
        """
        If the form is valid, log the user in and send verification emails for
        the user's email address and the given public contact email.
        """
        response = super().form_valid(form)
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            login(self.request, user)
        for email_address in {user.email, self.object.public_contact_email}:
            if not EmailAddress.objects.filter(email=email_address).exists():
                email = EmailAddress.objects.create_unconfirmed(email_address, user)
                send_email_verification(email, self.request)
        return response

    def get_form_kwargs(self):
        kwargs = super(BetaTestApplicationView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

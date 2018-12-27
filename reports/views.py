# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
Views for Invoices Reports
"""
import calendar
from datetime import datetime

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from reports.helpers import generate_watched_forks_instances, generate_charges
from userprofile.models import Organization


@user_passes_test(lambda u: u.is_superuser)
def report(request, organization, year, month):
    """
    Report view
    """
    try:
        invoice_start_date = timezone.make_aware(datetime(int(year), int(month), 1))
    except ValueError:
        return HttpResponseBadRequest(
            content='<h1>Bad Request</h1>'
                    '<p>Error when processing given date, consider using parameters within range</p>'
        )

    organization = get_object_or_404(Organization, github_handle=organization)
    forks_instances = generate_watched_forks_instances(organization)
    billing_data, total = generate_charges(forks_instances, invoice_start_date)

    return render(request, 'report.html', context={
        'year': year,
        'month': month,
        'month_name': calendar.month_name[int(month)],
        'organization': organization,
        'billing_data': billing_data,
        'total': total,
    })

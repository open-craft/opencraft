# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-01-05 17:04
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Func, F, Value
from django.db.models.functions import Lower


def clean_domain_name(field_name):
    """
    Returns a Django query expression that replaces all underscores with a
    hyphen, removes leading and trailing hyphens, and converts the field to
    lower case.
    """
    remove_underscores = Func(
        F(field_name),
        Value('_'),
        Value('-'),
        function='replace'
    )
    trim_hyphens = Func(
        remove_underscores,
        Value('-'),
        function='btrim',
    )
    remove_trailing_hyphens = Func(
        trim_hyphens,
        Value(r'[-]+\.'),
        Value('.'),
        Value('g'),
        function='regexp_replace'
    )
    return Lower(remove_trailing_hyphens)


def fix_invalid_domain_names(apps, schema_editor):
    BetaTestApplication = apps.get_model('registration', 'BetaTestApplication')
    OpenEdXInstance = apps.get_model('instance', 'OpenEdXInstance')

    BetaTestApplication.objects.update(subdomain=clean_domain_name('subdomain'))
    OpenEdXInstance.objects.update(
        internal_lms_domain=clean_domain_name('internal_lms_domain'),
        internal_lms_preview_domain=clean_domain_name('internal_lms_preview_domain'),
        internal_studio_domain=clean_domain_name('internal_studio_domain'),
        internal_discovery_domain=clean_domain_name('internal_discovery_domain'),
        internal_ecommerce_domain=clean_domain_name('internal_ecommerce_domain'),
    )


def migrate_noop(apps, schema_editor):
    # Cannot reverse the data migration, so just no-op
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('registration', '0006_auto_20180105_1631'),
    ]

    operations = [
    ]

# -*- coding: utf-8 -*-
import sys
from django.db import migrations, models
from instance.models.instance import OpenEdXInstance as OpenEdXInstance


def reset_ansible_settings(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    # Note that we are using the current version of OpenEdXInstance instead of the historical
    # version from the app registry, since the faked version from the registry doesn't have any of
    # the custom fields and methods.  I don't think there is any better way to do this.  Migrations
    # are a terrible hack.
    for instance in OpenEdXInstance.objects.using(db_alias).iterator():
        if not instance.ansible_settings:
            try:
                instance.reset_ansible_settings(commit=True)
            except Exception as exc:
                print('Error while migrating {}: {}'.format(instance, exc), file=sys.stderr)
                print('Ignoring error and carrying on.', file=sys.stderr)


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0034_auto_20151022_1652'),
    ]

    operations = [
        migrations.RunPython(reset_ansible_settings, migrations.RunPython.noop),
    ]

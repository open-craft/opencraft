# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('instance', '0027_auto_20150920_1357'),
    ]

    operations = [
        migrations.RenameField('InstanceLogEntry', 'instance', 'obj'),
        migrations.RenameField('ServerLogEntry', 'server', 'obj'),
    ]

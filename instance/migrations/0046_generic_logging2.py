# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, migrations, models
import django_extensions.db.fields
import instance.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('instance', '0045_generic_logging1'),
    ]

    def data_forward(apps, schema_editor):
        """
        Copy log entries from GeneralLogEntry, InstanceLogEntry, and ServerLogEntry into the new
        combined LogEntry table.
        """
        ContentType = apps.get_model("contenttypes", "ContentType")
        instance_type = ContentType.objects.get_for_model(apps.get_model('instance', 'singlevmopenedxinstance'))
        server_type = ContentType.objects.get_for_model(apps.get_model('instance', 'openstackserver'))
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO instance_logentry (created, modified, text, level)
            SELECT created, modified, text, level FROM instance_generallogentry
            """
        )

        cursor.execute(
            """
            INSERT INTO instance_logentry (created, modified, text, level, content_type_id, object_id)
            SELECT created, modified, text, level, %s, obj_id FROM instance_instancelogentry
            """,
            [instance_type.pk]
        )

        cursor.execute(
            """
            INSERT INTO instance_logentry (created, modified, text, level, content_type_id, object_id)
            SELECT created, modified, text, level, %s, obj_id FROM instance_serverlogentry
            """,
            [server_type.pk]
        )

    def data_backward(apps, schema_editor):
        """
        Reverse the data migration
        """
        ContentType = apps.get_model("contenttypes", "ContentType")
        instance_type = ContentType.objects.get_for_model(apps.get_model('instance', 'singlevmopenedxinstance'))
        server_type = ContentType.objects.get_for_model(apps.get_model('instance', 'openstackserver'))
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO instance_generallogentry (created, modified, text, level)
            SELECT created, modified, text, level FROM instance_logentry WHERE content_type_id IS NULL
            """
        )

        cursor.execute(
            """
            INSERT INTO instance_instancelogentry (created, modified, text, level, obj_id)
            SELECT created, modified, text, level, object_id FROM instance_logentry WHERE content_type_id = %s
            """,
            [instance_type.pk]
        )

        cursor.execute(
            """
            INSERT INTO instance_serverlogentry (created, modified, text, level, obj_id)
            SELECT created, modified, text, level, object_id FROM instance_logentry WHERE content_type_id = %s
            """,
            [server_type.pk]
        )

    operations = [
        migrations.RunPython(data_forward, data_backward),
    ]

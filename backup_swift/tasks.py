import datetime

from backup_swift.tarsnap import run_tarsnap
from django.core.mail import mail_admins
from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task
from opencraft import settings
from instance import openstack

if settings.BACKUP_SWIFT_ENABLED:

    @db_periodic_task(crontab(minute=10, hour=0))
    def backup_swift_task():
        error_report = ""

        download_results = openstack.download_swift_account(settings.BACKUP_SWIFT_TARGET)

        if download_results:
            error_report += "Following containers failed to download\n"
            for container in download_results:
                error_report += "#. {name}; Failed files: {count}.".format(
                    name=container.name, count=container.number_of_failures
                )

        tarsnap_erors = run_tarsnap(
            keyfile=settings.BACKUP_SWIFT_TARSNAP_KEY_LOCATION,
            cachedir=settings.BACKUP_SWIFT_TARSNAP_CACHE_LOCATION,
            directory=settings.BACKUP_SWIFT_TARGET,
            archive_name="{}-{}".format(settings.BACKUP_SWIFT_TARSNAP_KEY_ARCHIVE_NAME, datetime.datetime.now().isoformat())
        )

        if tarsnap_erors:
            error_report += '\n'
            error_report += tarsnap_erors

        if error_report:
            mail_admins("Error when backing up swift containers", error_report)
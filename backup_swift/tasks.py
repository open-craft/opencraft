import datetime

from backup_swift.tarsnap import run_tarsnap
from django.core.mail import mail_admins
from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task, db_task
from opencraft import settings
from instance import openstack

from . import utils


def do_backup_swift():
    error_report = ""

    # TODO: Add try catch to handle misc exceptions, treat them as fatal.
    download_results = openstack.download_swift_account(settings.BACKUP_SWIFT_TARGET)

    if download_results:
        error_report += "Following containers failed to download\n"
        for container in download_results:
            error_report += "#. {name}; Failed files: {count}.".format(
                name=container.name, count=container.number_of_failures
            )

    tarsnap_errors = run_tarsnap(
        keyfile=settings.BACKUP_SWIFT_TARSNAP_KEY_LOCATION,
        cachedir=settings.BACKUP_SWIFT_TARSNAP_CACHE_LOCATION,
        directory=settings.BACKUP_SWIFT_TARGET,
        archive_name="{}-{}".format(settings.BACKUP_SWIFT_TARSNAP_KEY_ARCHIVE_NAME, datetime.datetime.now().isoformat())
    )

    if tarsnap_errors:
        error_report += "Error while running tarsnap"

    if error_report:
        mail_admins("Error when backing up swift containers", error_report)

    if settings.BACKUP_SWIFT_SNITCH:
        utils.ping_heartbeat_url(settings.BACKUP_SWIFT_SNITCH)

    print(error_report)


@db_task()
def backup_swift_task():
    do_backup_swift()

if settings.BACKUP_SWIFT_ENABLED:

    # This is long running task, more like spawn_appserver than watch_pr,
    # since we a single queue for periodic tasks it makes sense for this to finish
    # early and then execute in another worker.
    @db_periodic_task(crontab(minute="*", hour="*"))
    def backup_swift_periodic():
        backup_swift_task()
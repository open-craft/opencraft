"""
Worker tasks for reporting
"""

# Imports #####################################################################

from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management import call_command
from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task

from instance.models.openedx_instance import OpenEdXInstance


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

# Defaults to '0 2 1 * *' which is the first of every month at 2AM UTC
TRIAL_INSTANCES_REPORT_SCHEDULE = getattr(settings, 'TRIAL_INSTANCES_REPORT_SCHEDULE',
                                          '0 2 1 * *').split()

TRIAL_INSTANCES_REPORT_SCHEDULE_MINUTE = TRIAL_INSTANCES_REPORT_SCHEDULE[0]
TRIAL_INSTANCES_REPORT_SCHEDULE_HOUR = TRIAL_INSTANCES_REPORT_SCHEDULE[1]
TRIAL_INSTANCES_REPORT_SCHEDULE_DAY = TRIAL_INSTANCES_REPORT_SCHEDULE[2]
TRIAL_INSTANCES_REPORT_SCHEDULE_MONTH = TRIAL_INSTANCES_REPORT_SCHEDULE[3]
TRIAL_INSTANCES_REPORT_SCHEDULE_DAY_OF_WEEK = TRIAL_INSTANCES_REPORT_SCHEDULE[4]


# Tasks #######################################################################

# Run on the 1st of every month
@db_periodic_task(
    crontab(
        minute=TRIAL_INSTANCES_REPORT_SCHEDULE_MINUTE,
        hour=TRIAL_INSTANCES_REPORT_SCHEDULE_HOUR,
        day=TRIAL_INSTANCES_REPORT_SCHEDULE_DAY,
        month=TRIAL_INSTANCES_REPORT_SCHEDULE_MONTH,
        day_of_week=TRIAL_INSTANCES_REPORT_SCHEDULE_DAY_OF_WEEK
    )
)
def send_trial_instances_report(recipients=settings.TRIAL_INSTANCES_REPORT_RECIPIENTS):
    """
    Generate and send a trial instance data report for the past month

    This task runs on the first of every month at 2AM
    """

    if not recipients:
        logger.warning('No recipients listed for Trial Instances Report. It will not be generated.')
        return True

    # Start with the beginning of this month
    beginning_of_this_month = datetime.utcnow().date().replace(day=1)

    # Get last month by subtracting one day from the beginning of
    # this month to get the last day of last month
    # Finally, replace the day with 1, to get the first day of last month
    end_of_last_month = (beginning_of_this_month - timedelta(days=1))
    beginning_of_last_month = end_of_last_month.replace(day=1)

    # Get instances with an active betatestapplication,
    # whose InstanceReference has an active OpenEdXAppServer
    # and was created last month
    instances = OpenEdXInstance.objects.exclude(
        betatestapplication__isnull=True
    ).filter(
        ref_set__openedxappserver_set___is_active=True
    ).filter(
        ref_set__created__range=[
            beginning_of_last_month.strftime("%Y-%m-%d 00:00:00"),
            end_of_last_month.strftime("%Y-%m-%d 23:59:59")
        ]
    )
    domains = [
        instance.external_lms_domain or instance.internal_lms_domain for instance in instances
    ]
    csv_filename = '/tmp/trial_instances_report.csv'

    email_subject = "{month_and_year} Trial Instances".format(
        month_and_year=end_of_last_month.strftime("%B %Y")
    )

    try:
        call_command(
            'instance_statistics_csv',
            out=csv_filename,
            domains=','.join(domains),
            start_date=beginning_of_last_month.strftime("%Y-%m-%d"),
            end_date=end_of_last_month.strftime("%Y-%m-%d")
        )
    except SystemExit:
        # The command exited prematurely. Send failure email to recipients
        logger.error('`instance_statistics_csv` command failed. Sending notification email')
        email_subject += ' Failure'
        email = EmailMessage(
            email_subject,
            'Unable to generate a Trial Instances Report due to failure of `instance_statistics_csv` command',
            settings.DEFAULT_FROM_EMAIL,
            recipients
        )
        email.send()
        return False

    text_message = (
        'Please find attached a CSV with the statistics for '
        '{month_and_year} for all instances with an active '
        'Beta Test Application'.format(
            month_and_year=end_of_last_month.strftime("%B %Y")
        )
    )

    email = EmailMessage(
        email_subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        recipients
    )

    email.attach_file(csv_filename)

    return email.send()

# Run on the 1st of every month
@db_periodic_task(
    crontab(
        minute=TRIAL_INSTANCES_REPORT_SCHEDULE_MINUTE,
        hour=TRIAL_INSTANCES_REPORT_SCHEDULE_HOUR,
        day=TRIAL_INSTANCES_REPORT_SCHEDULE_DAY,
        month=TRIAL_INSTANCES_REPORT_SCHEDULE_MONTH,
        day_of_week=TRIAL_INSTANCES_REPORT_SCHEDULE_DAY_OF_WEEK
    )
)
def send_instances_active_users_report(recipients=settings.TRIAL_INSTANCES_REPORT_RECIPIENTS):
    """
    Generate and send a report for all instances the past month

    This task runs on the first of every month at 2AM
    """

    if not recipients:
        logger.warning('No recipients listed for Active Instances Report. It will not be generated.')
        return True

    # Start with the beginning of this month
    beginning_of_this_month = datetime.utcnow().date().replace(day=1)

    # Get last month by subtracting one day from the beginning of
    # this month to get the last day of last month
    # Finally, replace the day with 1, to get the first day of last month
    end_of_last_month = (beginning_of_this_month - timedelta(days=1))
    beginning_of_last_month = end_of_last_month.replace(day=1)

    # Get all instances whose InstanceReference has an active OpenEdXAppServer
    instances = OpenEdXInstance.objects.filter(
        ref_set__openedxappserver_set___is_active=True
    )
    domains = [
        instance.external_lms_domain or instance.internal_lms_domain for instance in instances
    ]
    csv_filename = '/tmp/active_instances_report.csv'

    email_subject = "{month_and_year} Active Users for Instances".format(
        month_and_year=end_of_last_month.strftime("%B %Y")
    )

    try:
        call_command(
            'instance_statistics_csv',
            out=csv_filename,
            users=True,
            domains=','.join(domains),
            start_date=beginning_of_last_month.strftime("%Y-%m-%d"),
            end_date=end_of_last_month.strftime("%Y-%m-%d")
        )
    except SystemExit:
        # The command exited prematurely. Send failure email to recipients
        logger.error('`instance_statistics_csv` command failed. Sending notification email')
        email_subject += ' Failure'
        email = EmailMessage(
            email_subject,
            'Unable to generate a Active Instances Report due to failure of `instance_statistics_csv` command',
            settings.DEFAULT_FROM_EMAIL,
            recipients
        )
        email.send()
        return False

    text_message = (
        'Please find attached a CSV with the active user statistics for '
        '{month_and_year} for all instances'.format(
            month_and_year=end_of_last_month.strftime("%B %Y")
        )
    )

    email = EmailMessage(
        email_subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        recipients
    )

    email.attach_file(csv_filename)

    return email.send()

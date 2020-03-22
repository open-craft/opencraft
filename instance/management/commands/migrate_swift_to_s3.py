# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
Migrate SWIFT assets to S3.
One-time script.


Detailed process to migrate 1 server:
- download all SWIFT files to your local computer with rclone, as a reference, as a backup and as a guide to know what
  you'll be copying. Take note of particular patterns in the file names and the types of files used
- check the current swift/s3 storage settings of the instance to migrate (verify that S3 is still not set up)
- manually modify the .filter() in this script to find the IDs of the instances to migrate
- also set the region (use Ireland)
- enable all conditional parts (change the "if 0:" to "if 1:") the first time. When you re-run it you may use this to
  skip some migration steps or for debugging
- run script, from Ocim production (just place the file and run it, no need to change branches). The command is:
  honcho -e .env run ./manage.py migrate_swift_to_s3
- let the script copy everything, watch for errors, re-run if it fails (some AWS things take time and you may need
  to wait some seconds between re-runs). If it fails, it's safe to retry it, since it won't delete the old data:
  it will create S3 resources and copy data to S3, but still won't use it until you deploy new servers. You can
  safely remove the new S3 files and re-run the script in case something breaks in the middle, or just re-run to
  make rclone copy the missing files
- when the script successfully copies files, let it save() the instance with the new settings
- check settings and deploy a new server with the blue button
- wait 2 h
- test the new server through the internal link
- to be extra careful: download the files from SWIFT again and compare them with the first download (you can use a tool
  like dirdiff). If they differ, it means that files changed during those 2 h. You can re-run this script (you can
  skip some steps in re-runs, like the bucket creation and user creation) and this will cause a 2nd SWIFT→S3
  synchronization and it will keep files up to date. Verify that files match now. Test the server and activate it
- if the server doesn't work, don't activate it; restore storage_type to swift (you may delete the IAM user and bucket
  too, from the AWS web interface)
- if the instance has high activity or constantly moving files, do a final sync after you activated the new server (from
  the deactivated server to the activated one). Or you could have scheduled a downtime for this
- don't delete old files from the SWIFT container (from OVH) and don't delete the container. The container could have
  been used to create URLs for uploaded images that are linked from forum posts. These URLs still point to SWIFT, and
  you don't want to go through mongo fixing the posts. Don't delete SWIFT settings from the OpenEdXInstance object
  either; it's better to leave them as they were, to show that the SWIFT container still exists
- delete ~/.config/rclone/ if still there
"""

# Imports #####################################################################

import logging
import re
import subprocess
import swiftclient

from django.core.management.base import BaseCommand
from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)

# Desired destination region for S3 bucket.
# This will be saved in instance.s3_region
# Different regions have different requirements
# see https://docs.google.com/document/d/1H8iUa05nSD6puQQoUf3DTfPb3gtUFGKtKjUNMKoWAAg/edit#
#
# Recommended: '' (default) and 'eu-west-1' (Ireland)
S3_REGION = 'eu-west-1'

# Classes #####################################################################

# We don't have unit tests for this command ("no cover" disables test coverage in the class) because it uses
# too many network tools and processes involved that aren't worth mocking: rclone file transfers,
# creation of rclone config files, IAM user and S3 bucket creation. There are already some "assert" that do
# basic sanity checks.
# The best way to test the script is by running it against some servers and verifying that it moves all files.


class Command(BaseCommand):  # pragma: no cover
    """
    Migrate SWIFT to S3.
    """
    help = (
        'Migrate a server\'s data from SWIFT to S3.'
    )

    def __init__(self, *args, **kwargs):
        """
        Some unused options.
        """
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}
        self.retried = {}

    @staticmethod
    def _get_swift_connection(instance):
        """
        Get Connection object.
        """
        return swiftclient.Connection(
            user=instance.swift_openstack_user,
            key=instance.swift_openstack_password,
            authurl=instance.swift_openstack_auth_url,
            tenant_name=instance.swift_openstack_tenant,
            auth_version='3',
            os_options={'region_name': instance.swift_openstack_region}
        )

    @staticmethod
    def _create_rclone_config_s3(instance):
        """
        Creates rclone config, for S3.
        """
        rclone_config = (
            "rclone config create ocim-s3 s3 access_key_id '%s' secret_access_key '%s' region '%s'" % (
                instance.s3_access_key,
                instance.s3_secret_access_key,
                S3_REGION
            )
        )
        # LOG.info("Will run this command: %s", rclone_config)
        subprocess.Popen(rclone_config, shell=True)

    @staticmethod
    def _create_rclone_config_swift(instance):
        """
        Creates rclone config, for SWIFT.
        """
        rclone_config = (
            "rclone config create ocim-swift swift "
            "user '%s' key '%s' auth '%s' tenant '%s' auth_version '3' region '%s'" % (
                instance.swift_openstack_user,
                instance.swift_openstack_password,
                instance.swift_openstack_auth_url,
                instance.swift_openstack_tenant,
                instance.swift_openstack_region,
            )
        )

        # LOG.info("Will run this command: %s", rclone_config)
        subprocess.Popen(rclone_config, shell=True)

    @staticmethod
    def _delete_rclone_configs():
        """
        Remove temporary configs used during the migration.
        """
        subprocess.Popen("rclone config delete ocim-swift", shell=True)
        subprocess.Popen("rclone config delete ocim-s3", shell=True)

    @staticmethod
    def _copy_subdirectory(key_name, new_name, swift_container, s3_bucket):
        """
        Copy subdirectory using rclone
        """
        LOG.info("%s ---> %s", key_name, new_name)
        assert not new_name.startswith('/')
        assert s3_bucket

        command = "rclone copy -v ocim-swift:%s/%s ocim-s3:%s/%s" % (swift_container, key_name, s3_bucket, new_name)
        LOG.info("Will run this command: %s", command)
        p = subprocess.Popen(command, shell=True)
        p.communicate()
        p.wait()
        # LOG.info("Command output: ", output)

    # This is a long process with many steps and we don't gain much by moving steps to separate functions
    # pylint: disable=too-many-statements,too-many-branches, useless-suppression
    def _migrate_swift_to_s3(self, instance):
        """Create IAM user, S3 bucket, move all files from SWIFT to S3, and mark the instance as using S3."""
        # It still doesn't do error handling, so the first times you must review that it's doing the right thing
        # A re-run might be needed if AWS takes longer than usual to make the user/bucket available.
        # But normally the migration works in one run.

        # Check sanity
        assert instance.storage_type == 'swift'
        assert instance.swift_container_name

        # You may enable/disable many of these sections while testing or re-running, by changing 0 to 1
        if 1:  # pylint: disable=using-constant-test
            LOG.info("Creating IAM user")
            assert not instance.s3_access_key
            assert not instance.s3_secret_access_key

            # The bucket name must be set before creating the user, to limit the user to that bucket
            # Note that bucket names could be different S3 (e.g. instance.bucket transforms _ to -)
            instance.s3_bucket_name = instance.bucket_name

            # Debug only: use different names each time (otherwise AWS complains with HTTP 409 error)
            # instance.s3_bucket_name = "%s-%i" % (instance.s3_bucket_name, int(time.time()))

            instance.save()

            instance.create_iam_user()
            assert instance.s3_access_key
            assert instance.s3_secret_access_key

        if 1:  # pylint: disable=using-constant-test
            LOG.info("Creating bucket (%s). Waiting some seconds between attempts", instance.s3_bucket_name)
            # This private method doesn't have a public version
            instance._create_bucket(retry_delay=6, attempts=8, location=S3_REGION)

        LOG.info("Preparing rclone")
        # Doesn't hurt to run it several times (it will overwrite old one)
        self._create_rclone_config_s3(instance)
        self._create_rclone_config_swift(instance)

        swift = self._get_swift_connection(instance)

        LOG.info("Migrating container: %s", instance.swift_container_name)

        # This list includes all root files, directories and files contained in directories
        # E.g. 'a.jpg', 'submissions_attachmentsbadges/', 'submissions_attachmentsbadges/something.jpg',
        # 'submissions_attachmentsbadges/folder/', 'submissions_attachmentsbadges/folder/some.pdf'

        all_files = swift.get_container(instance.swift_container_name)[1]
        # LOG.info("All files: ", all_files)

        # We'll iterate through each root file/directory. rclone already copies the subdirectories inside a dir.
        copied = []

        for item in all_files:
            # Get only directory name
            # e.g. 'submissions_attachmentsbadges/folder/some.pdf' -> 'submissions_attachmentsbadges'
            # or 'file.pdf' -> 'file.pdf' (unchanged)
            # Rclone will copy the contents inside
            base_name = re.sub('/.*', '', item['name'])

            LOG.info("PROGRESS: Name: %s. Directory name: %s. Copied: %s", item['name'], base_name, copied)

            # Avoid copying 'submissions_attachmentsbadges/folder/some.pdf' because it was already copied
            # as part of 'submissions_attachmentsbadges'
            if base_name in copied:
                LOG.info("Skipping %s", base_name)
                continue

            # replace new name if they contain submissions_attachments (there is a bug on swift implementation that
            # makes files be uploaded to the wrong directory)
            # The changes to do are like:
            #   submissions_attachmentsbadges/ ---> submissions_attachments/badges
            #   submissions_attachmentsuser_tasks/ ---> submissions_attachments/user_tasks
            # etc. and in addition there's a special case
            #   submissions_attachmentssubmissions_attachments ---> submissions_attachments
            # This part can be expanded as we find new cases through different servers
            new_name = re.sub(r'^(submissions_attachments)/?', r'\g<1>/', base_name)
            if new_name == 'submissions_attachments/submissions_attachments':
                # special case. These files inside the submissions_attachments directory itself
                new_name = 'submissions_attachments'

            # You may require to uncomment this depending on whether organization logos should be
            # inside or outside submissions_attachments. SWIFT stored it inside (in a folder
            # called "submissions_attachmentsorganization_logos") but some AWS URL was looking for
            # them outside. To be tested
            # elif new_name == 'submissions_attachments/organization_logos':
            #     new_name = 'organization_logos'

            # There's a special case which won't work and is tricky to implement: when a file is called
            # e.g. "submissions_attachments15100382041175505.jpg" (this happens with images uploaded to the forum).
            # In this case, the command to execute will be like:
            #   rclone copy -v ocim-swift:hda_opencraft_hosting/submissions_attachments15100382041175505.jpg \
            #                ocim-s3:ocim-hda-opencraft-hosting/submissions_attachments/15100382041175505.jpg
            # and unfortunately this will create a *directory* called "submissions_attachments/15100382041175505.jpg",
            # with the file submissions_attachments15100382041175505.jpg in it. So the final path will be:
            # submissions_attachments/15100382041175505.jpg/submissions_attachments15100382041175505.jpg
            #
            # Note that rclone's "sync" doesn't seem to rename files, so another method would be needed.
            # Instead of fixing this, don't fix it. Some reasons:
            # - The original file is part of a URL that includes submissions_attachments15100382041175505.jpg,
            #   so it's not an error anymore, it's the official URL, and if you fix it by adding
            #   an / it won't be the same URL
            # - Forum posts in mongo will still be pointing to the SWIFT URL, not to AWS, so noone cares about the
            #   S3 URL (i.e. the new one) nor about whether it has a / or not. Verified by connecting to mongo and
            #  checking that the post stores the full URL with the SWIFT hostname)
            #

            # There's another special case: we use a different "COMMON_OBJECT_STORE_LOG_SYNC_PREFIX" for SWIFT and S3
            # In SWIFT without prefix (e.g. "logs/tracking"), in AWS with prefix (e.g. "some_host_name/logs/tracking")
            # Real example:
            # SWIFT: logs/tracking/i-00a5488f-149.202.175.112/tracking.log
            #    S3: ajtest_opencraft_hosting/logs/tracking/edxapp-appserver/i-00bb2dec-213.32.77.144/tracking.log
            #
            if new_name == 'logs':
                new_name = '{}/{}'.format(instance.swift_container_name, 'logs')

            # There's another difference in logs synced to SWIFT and S3: note the infix "edxapp-appserver" in
            # "ajtest_opencraft_hosting/logs/tracking/edxapp-appserver/i-00bb2dec-213.32.77.144/tracking.log".
            # This is our security group name, and it's added by send-logs-to-s3 but not by send-logs-to-swift
            # It's not very important because when Insights reads tracking logs, it will find them even if they're
            # in subfolders. So we don't need to transform the new path here.

            self._copy_subdirectory(
                base_name,
                new_name,
                swift_container=instance.swift_container_name,
                s3_bucket=instance.s3_bucket_name
            )

            copied.append(base_name)

        LOG.info("Migrated! Copied: %i items. Full list: %s", len(copied), copied)

        if 1:  # pylint: disable=using-constant-test
            LOG.info("Cleaning rclone configs")
            self._delete_rclone_configs()

        if 1:  # pylint: disable=using-constant-test
            LOG.info("Did everything work? To change this instance to S3 type, press ENTER")
            input()
            instance.storage_type = 's3'
            instance.s3_region = S3_REGION
            instance.save()
            # This could be automated if it will save work
            LOG.info("Please spawn a server yourself for instance %i, then test it and activate it", instance.id)

        if 0:  # pylint: disable=using-constant-test
            LOG.info("Debug only! Press ENTER to delete IAM & bucket and clear those settings in the instance, "
                     "and set it back to SWIFT. Then you can test this migration again and again. Or press C-c to end")
            input()
            LOG.info("Deprovisioning S3...")
            instance.deprovision_s3()
            instance.storage_type = 'swift'
            instance.save()
            LOG.info("We're back to SWIFT")

    def handle(self, *args, **options):
        """
        Finds all instances and migrates them.
        """
        self.logger.warning('SWIFT storage is not maintained and will be dropped in a future version.')
        self.options = options

        # instances = OpenEdXInstance.objects.filter(storage_type='swift')

        # You can use this to choose the IDs (or any other filter), and migrate in batches.
        # You must add the instance IDs directly in the code. For example: .filter(id__in=[1111, 1120, ])
        instances = OpenEdXInstance.objects.filter(id__in=[])

        LOG.info("Will migrate %i instances", instances.count())
        for instance in instances:
            self._migrate_swift_to_s3(instance)

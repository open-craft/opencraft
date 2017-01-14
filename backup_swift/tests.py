"""Tests module for the backup_swift_app"""
import subprocess
from logging import LogRecord
from unittest import mock

from django.core.management import call_command
from django.test.testcases import TestCase
from django.test.utils import override_settings
from swiftclient.service import SwiftError
import requests

from backup_swift.tasks import do_backup_swift, backup_swift_periodic, backup_swift_task
from backup_swift.utils import filter_swift
from . import tarsnap, tasks
from instance.openstack_utils import FailedContainer


@mock.patch('subprocess.run')
class RunTarsnapCommandTestCase(TestCase):
    """
    Test case for run_tarsnap_command function
    """

    TARSNAP_COMMAND = ['tarsnap', '--keyfile', '/etc/keyfile', '--cachedir', '/var/cache/tarsnap']

    def run_basic_checks(self, run):
        """Basic checks."""
        run.assert_called_once_with(self.TARSNAP_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_run_tarsnap_command_positive_case(self, run):
        """Test of happy path, where tarsnap executes without errors."""
        run.return_value = subprocess.CompletedProcess(self.TARSNAP_COMMAND, 0)

        tarsnap.run_tarsnap_command(self.TARSNAP_COMMAND)
        self.run_basic_checks(run)

    def test_run_tarsnap_command_error_case(self, run):
        """Test for a miscellaneous failure."""
        run.return_value = subprocess.CompletedProcess(self.TARSNAP_COMMAND, 1, b"Permission Denied: /etc/keyfile")

        with self.assertRaises(tarsnap.TarsnapException):
            tarsnap.run_tarsnap_command(self.TARSNAP_COMMAND)

        self.run_basic_checks(run)

    def test_run_tarsnap_command_fsck_error(self, run):
        """Test error asking to run --fsck."""
        run.return_value = subprocess.CompletedProcess(
            self.TARSNAP_COMMAND, 1, b"Sequence no mismatch, please run --fsck to correct")

        with self.assertRaises(tarsnap.TarsnapFsckException):
            tarsnap.run_tarsnap_command(self.TARSNAP_COMMAND)

        self.run_basic_checks(run)


class TarsnapBackupTestCase(TestCase):
    """Tests for performing tarsnap backups."""

    KEYFILE = '/etc/tarsnap.key'
    CACHEDIR = '/var/cache/tarsnap'
    BACKUP_DIRECTORY = '/var/cache/backups'
    ARCHIVE_NAME = 'backup-19850919'

    BACKUP_COMMAND = [
        'tarsnap', '--keyfile', KEYFILE, '--cachedir', CACHEDIR, '-c', '-f', ARCHIVE_NAME, BACKUP_DIRECTORY
    ]
    FSCK_COMMAND = ['tarsnap', '--keyfile', KEYFILE, '--cachedir', CACHEDIR, '--fsck']

    def do_test_backup(self, run_command_outputs, run_command_calls, expected_backup_output):
        """
        Actual method performing checks
        :param list run_command_outputs: List of side effects for subsequent calls to  run_tarsnap_command
        :param list run_command_calls: List of expected calls to run_tarsnap_command
        :param bool expected_backup_output: Expected output of the backup.
        """
        with mock.patch("backup_swift.tarsnap.run_tarsnap_command") as run_command:
            run_command.side_effect = run_command_outputs
            result = tarsnap.make_tarsnap_backup(self.KEYFILE, self.CACHEDIR, self.ARCHIVE_NAME, self.BACKUP_DIRECTORY)
            self.assertEqual(run_command.call_args_list, run_command_calls)
            self.assertEqual(result, expected_backup_output)

    def test_positive_case(self):
        """Test for backup that works. """
        run_command_outputs = [
            # A single call that does not return any error.
            None
        ]
        self.do_test_backup(run_command_outputs, [mock.call(self.BACKUP_COMMAND)], True)

    def test_imminent_error_case(self):
        """Test for case where first error is unrecoverable """
        exception = tarsnap.TarsnapException(
            subprocess.CalledProcessError('1', self.BACKUP_COMMAND, output="No such file or directory"))

        self.do_test_backup([exception], [mock.call(self.BACKUP_COMMAND)], False)

    def test_error_recovered(self):
        """Test for a case where first error is recoverable, we recover by --fsck and then do backup successfully"""

        exception = tarsnap.TarsnapFsckException(
            subprocess.CompletedProcess(self.BACKUP_COMMAND, 1, stdout="Please run --fsck"))
        calls = [
            mock.call(self.BACKUP_COMMAND),
            mock.call(self.FSCK_COMMAND),
            mock.call(self.BACKUP_COMMAND)
        ]
        self.do_test_backup([exception, None, None], calls, True)

    def test_error_during_fsck(self):
        """Test for a case when we are trying to recover, but fail."""
        exception = tarsnap.TarsnapFsckException(
            subprocess.CompletedProcess(self.BACKUP_COMMAND, 1, stdout="Please run --fsck"))
        fsck_exception = tarsnap.TarsnapException(
            subprocess.CompletedProcess(self.FSCK_COMMAND, 1, stdout="Error during fsck"))
        calls = [
            mock.call(self.BACKUP_COMMAND),
            mock.call(self.FSCK_COMMAND)
        ]
        self.do_test_backup([exception, fsck_exception, None], calls, False)

    def test_error_fatal_error(self):
        """Test for a case when we are trying to recover, but fail."""
        exception = tarsnap.TarsnapFsckException(
            subprocess.CompletedProcess(self.BACKUP_COMMAND, 1, stdout="Please run --fsck"))
        fatal_exception = tarsnap.TarsnapException(
            subprocess.CompletedProcess(self.FSCK_COMMAND, 1, stdout="Fatal error"))
        calls = [
            mock.call(self.BACKUP_COMMAND),
            mock.call(self.FSCK_COMMAND),
            mock.call(self.BACKUP_COMMAND)
        ]
        self.do_test_backup([exception, None, fatal_exception], calls, False)


class TestPingHeartbeat(TestCase):
    """Tests for ping heartbeat url"""

    def test_positive_heartbeat(self):
        """Case where ping is succesfull."""
        with mock.patch('requests.get') as get:
            response = mock.MagicMock()
            response.status_code = 200
            get.return_value = response
            self.assertTrue(tasks.ping_heartbeat_url('http://example.com'))
            get.assert_called_once_with('http://example.com', timeout=30)

    def test_invalid_status_heartbeat(self):
        """Case where error status is returned."""
        with mock.patch('requests.get') as get:
            response = mock.MagicMock()
            response.status_code = 400
            get.return_value = response
            self.assertFalse(tasks.ping_heartbeat_url('http://example.com'))
            get.assert_called_once_with('http://example.com', timeout=30)

    def test_exception(self):
        """Case requests raises an exception."""
        with mock.patch('requests.get') as get:
            get.side_effect = requests.ConnectionError()
            self.assertFalse(tasks.ping_heartbeat_url('http://example.com'))
            get.assert_called_once_with('http://example.com', timeout=30)


@override_settings(
    BACKUP_SWIFT_ENABLED=True,
    BACKUP_SWIFT_TARGET='/var/cache/backups',
    BACKUP_SWIFT_TARSNAP_KEY_LOCATION='/etc/tarsnap.key',
    BACKUP_SWIFT_TARSNAP_CACHE_LOCATION='/var/cache/tarsnap',
    BACKUP_SWIFT_TARSNAP_KEY_ARCHIVE_NAME='im-swift-backup',
    BACKUP_SWIFT_SNITCH='http://example.com'
)
class TestBackupSequence(TestCase):
    """Test for whole backup sequence."""

    def add_patcher(self, patcher):
        """Helper method: adds and starts patcher."""
        self.patchers.append(patcher)
        return patcher.start()

    def setUp(self):
        """Sets up patchers."""
        self.patchers = []
        self.openstack_download = self.add_patcher(
            mock.patch("backup_swift.tasks.openstack_utils.download_swift_account")
        )
        self.tarsnap_backup = self.add_patcher(mock.patch("backup_swift.tasks.make_tarsnap_backup"))
        self.mail_admins = self.add_patcher(mock.patch("backup_swift.tasks.mail_admins"))
        self.heartbeat = self.add_patcher(mock.patch("backup_swift.tasks.ping_heartbeat_url"))

    def tearDown(self):
        """Stops patchers."""
        for patcher in self.patchers:
            patcher.stop()

    def test_happy_path(self):
        """Test for successful backup."""
        self.openstack_download.return_value = {}
        self.tarsnap_backup.return_value = True
        do_backup_swift()
        self.openstack_download.assert_called_once_with('/var/cache/backups')
        self.tarsnap_backup.assert_called_once_with(
            archive_name=mock.ANY,
            cachedir='/var/cache/tarsnap',
            directory='/var/cache/backups',
            keyfile='/etc/tarsnap.key'
        )
        archive_name = self.tarsnap_backup.call_args[1]['archive_name']
        self.assertTrue(archive_name.startswith("im-swift-backup-"))
        self.heartbeat.assert_called_once_with('http://example.com')
        self.mail_admins.assert_not_called()

    @override_settings(BACKUP_SWIFT_SNITCH=None)
    def test_happy_path_no_heartbeat(self):
        """Test for successful backup, without snitch set."""
        self.openstack_download.return_value = {}
        self.tarsnap_backup.return_value = True
        do_backup_swift()
        self.openstack_download.assert_called_once_with('/var/cache/backups')
        self.tarsnap_backup.assert_called_once_with(
            archive_name=mock.ANY,
            cachedir='/var/cache/tarsnap',
            directory='/var/cache/backups',
            keyfile='/etc/tarsnap.key'
        )
        archive_name = self.tarsnap_backup.call_args[1]['archive_name']
        self.assertTrue(archive_name.startswith("im-swift-backup-"))
        self.heartbeat.assert_not_called()
        self.mail_admins.assert_not_called()

    def test_swift_exception(self):
        """Test for case where swift raises an exception."""
        self.openstack_download.side_effect = SwiftError(None)
        self.tarsnap_backup.return_value = True
        do_backup_swift()
        self.openstack_download.assert_called_once_with('/var/cache/backups')
        self.assertTrue(self.tarsnap_backup.called)
        self.heartbeat.assert_not_called()
        self.mail_admins.assert_called_once_with(
            'Error when backing up swift containers',
            'Miscellaneous error while downloading swift containers\n'
            'Please check the server logs, they might contain more details.'
        )

    def test_swift_exception_and_tarsnap_exception(self):
        """Test for case where swift raises an exception, and then tarsnap fails too."""
        self.openstack_download.side_effect = SwiftError(None)
        self.tarsnap_backup.return_value = False
        do_backup_swift()
        self.openstack_download.assert_called_once_with('/var/cache/backups')
        self.assertTrue(self.tarsnap_backup.called)
        self.heartbeat.assert_not_called()
        report = (
            "Miscellaneous error while downloading swift containers\n"
            "Error while running tarsnap\n"
            'Please check the server logs, they might contain more details.'
        )
        self.mail_admins.assert_called_once_with(
            'Error when backing up swift containers',
            report
        )

    def test_swift_errors(self):
        """Test for case where some files couldn't be downloaded."""
        self.openstack_download.return_value = [
            FailedContainer('container-1', 10),
            FailedContainer('container-2', 5)
        ]
        self.tarsnap_backup.return_value = True
        do_backup_swift()
        self.openstack_download.assert_called_once_with('/var/cache/backups')
        self.assertTrue(self.tarsnap_backup.called)
        self.heartbeat.assert_not_called()
        report = (
            'Following containers failed to download:\n'
            '#. container-1; Failed files: 10.\n'
            '#. container-2; Failed files: 5.\n'
            'Please check the server logs, they might contain more details.'
        )
        self.mail_admins.assert_called_once_with(
            'Error when backing up swift containers',
            report
        )


# pylint: disable=no-self-use
class MiscTests(TestCase):
    """Tests for things that didn't deserve own class."""

    def test_log_filter(self):
        """filter_swift shouldn't filter this message."""
        record = LogRecord("test.logger", "WARN", "foo", 1000, "Foo %s", args=('arg', ), exc_info=None)
        self.assertTrue(filter_swift(record))

    def test_log_filter_positive(self):
        """filter_swift should filter this message."""
        message = (
            "Object GET failed: https://example.com/v1/"
            "auth/container/canary?multipart-manifest=get 304 Not Modified."
        )
        record = LogRecord("test.logger", "WARN", "foo", 1000, message, args=[], exc_info=None)
        self.assertFalse(filter_swift(record))

    def test_periodic_task(self):
        """Test that periodic task spawns backup_swift_task."""
        with mock.patch('backup_swift.tasks.backup_swift_task') as task:
            backup_swift_periodic()
            task.assert_called_once_with()

    def test_task(self):
        """Test that backup_swift_task calls do_backup_swift."""
        with mock.patch('backup_swift.tasks.do_backup_swift') as task:
            backup_swift_task()
            task.assert_called_once_with()

    def test_management_command(self):
        """Test that swift_backup management command calls do_backup_swift"""
        with mock.patch('backup_swift.tasks.do_backup_swift') as task:
            call_command('backup_swift')
            task.assert_called_once_with()

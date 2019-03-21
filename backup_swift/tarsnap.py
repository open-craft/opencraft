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
Tarsnap utilities
"""

# Imports #####################################################################

import logging
import subprocess

# Logging #####################################################################

logger = logging.getLogger(__name__)

# Exceptions ##################################################################


class TarsnapException(Exception):
    """Base class for tarsnap exceptions"""
    pass


class TarsnapFsckException(TarsnapException):
    """Exception raised when tarsnap suggests running --fsck to fix the error"""
    pass


# Functions ###################################################################


def run_tarsnap_command(command):
    """
    Run a tarsnap command.

    :param list[str] command:
    :raises TarsnapFsckException: If tarsnap suggests running ``--fsck``
    :raises TarsnapException: In case of any other error.
    """
    called_process = subprocess.run(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    if called_process.returncode == 0:
        return
    # tarsnap returns the same exit-code irregardless of what went wrong, but if problem can be solved
    # by running --fsck it is noted in the output.
    # We can't run --fsck every time, as it eats bandwidth and costs money.
    if b'--fsck' in called_process.stdout:
        raise TarsnapFsckException(called_process)
    raise TarsnapException(called_process)


def _run_tarsnap(keyfile, cachedir, archive_name, directory):
    """
    Tries to backup folder using tarsnap, handling cache mismatch running `--fsck`.

    :raises TarsnapException: In case of unrecoverable error.
    """

    common_command = ['tarsnap', '--keyfile', keyfile, '--cachedir', cachedir]
    create_archive_command = common_command + ['-c', '-f', archive_name, directory]
    fsck_command = common_command + ['--fsck']

    try:
        run_tarsnap_command(create_archive_command)
    except TarsnapFsckException:
        logger.info("Got tarsnap error. Trying to fix it by running tarsnap --fsck")
        run_tarsnap_command(fsck_command)
        run_tarsnap_command(create_archive_command)


def make_tarsnap_backup(keyfile, cachedir, archive_name, directory):
    """
    Function that runs tarsnap using `keyfile` and `cachedir`, to create archive named `archive_name`
    that contains contents of `directory`

    :param str keyfile: Keyfile to use by Tarsnap
    :param str cachedir: Cachedir to use by tarsnap
    :param str archive_name: Archive to create (note: tarsnap assumes unique archive names)
    :param str directory: Directory to archive
    """
    logger.info("Starting backup of following directory %s.", directory)
    try:
        _run_tarsnap(keyfile, cachedir, archive_name, directory)
        logger.info("Backup of %s successful.", directory)
        return True
    except TarsnapException as e:
        logger.error("Backup of %s failed, tarsnap stdout was %s", directory, e.args[0].stdout)
        return False

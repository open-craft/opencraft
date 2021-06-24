"""
Utilities for dealing with SSH.
"""
import logging
import subprocess

LOGGER = logging.getLogger(__name__)


def remove_known_host_key(ip: str):
    """
    Removes the known_hosts key entry for the given IP.

    :param ip: the IP of the entry to delete

    This doesn't check whether the entry existed.
    """
    LOGGER.info('Deleting the SSH host key of the server with the IP address "%s" from the SSH known hosts file.', ip)
    command = f'ssh-keygen -R {ip}'
    try:
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.SubprocessError:
        LOGGER.exception('Failed to delete the SSH host key of the server with the IP address "%s"', ip)

import subprocess


class TarsnapException(Exception):
    pass


class TarsnapFsckException(TarsnapException):
    pass


def _run_tarsnap_command(command):
    called_process = subprocess.run(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    # import pudb; pudb.set_trace()
    if called_process.returncode == 0:
        return
    if b'--fsck' in called_process.stdout:
        raise TarsnapFsckException(called_process)
    raise TarsnapException(called_process)


def _run_tarsnap(keyfile, cachedir, archive_name, directory):

    BASE_TARSNAP = ['tarsnap', '--keyfile', keyfile, '--cachedir', cachedir,]
    TARSNAP_CREATE = BASE_TARSNAP + ['-c',  '-f', archive_name, directory]
    TARSNAP_FSCK = BASE_TARSNAP + ['--fsck']

    try:
        _run_tarsnap_command(TARSNAP_CREATE)
        return
    except TarsnapFsckException:
        pass

    _run_tarsnap_command(TARSNAP_FSCK)
    _run_tarsnap_command(TARSNAP_CREATE)


def run_tarsnap(keyfile, cachedir, archive_name, directory):
    try:
        _run_tarsnap(keyfile, cachedir, archive_name, directory)
        return True
    except TarsnapException:
        return False
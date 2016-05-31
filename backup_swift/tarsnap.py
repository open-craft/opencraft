import subprocess


def run_tarsnap(keyfile, cachedir, archive_name, directory):
    # TODO: Handle problems with cache and run fsck then
    subprocess.check_call(['tarsnap', '--keyfile', keyfile, '--cachedir', cachedir, '-f', archive_name, directory])

    return ''
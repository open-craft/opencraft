from git.repo.base import Repo
from tempfile import mkdtemp

def get_repo_from_url(repo_url):
    # TODO: Delete the temporary directory after use
    return Repo.clone_from(repo_url, mkdtemp())

def clone_configuration_repo():
    # Cloning & remotes
    configuration_repo = get_repo_from_url('https://github.com/edx/configuration.git')
    opencraft_remote = configuration_repo.create_remote('opencraft',
                                                        'https://github.com/open-craft/configuration.git')
    opencraft_remote.fetch()

    # Merge the opencraft branch, which contains fixes to get the ansible scripts to run in our 
    # specific case, for example openstack fixes - it should be kept to a minimum and pushed upstream
    opencraft_branch = configuration_repo.create_head('opencraft', opencraft_remote.refs.opencraft)
    opencraft_branch.set_tracking_branch(opencraft_remote.refs.opencraft)
    configuration_repo.git.merge('opencraft')

    return configuration_repo.working_dir

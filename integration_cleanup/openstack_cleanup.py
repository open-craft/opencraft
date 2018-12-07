from datetime import datetime
from novaclient import client


class OpenStackCleanupInstance:
    """
    Handles the search and cleanup of all unused OpenStack resources used
    by CircleCI
    """
    def __init__(self, age_limit, openstack_settings, dry_run=False):
        """
        Set's up Nova client
        """
        self.dry_run = dry_run
        self.age_limit = age_limit
        self.cleaned_ips = []

        self.nova = client.Client(
            "2.0",
            auth_url=openstack_settings['auth_url'],
            username=openstack_settings['username'],
            api_key=openstack_settings['api_key'],
            project_id=openstack_settings['project_id'],
            region_name=openstack_settings['region_name']
        )

    def get_active_circle_ci_instances(self):
        """
        Returns list of active instances running on the OpenStack provider
        that have been created by CircleCI
        """
        return self.nova.servers.list(
            search_opts={
                'key_name': 'circleci'
            }
        )

    def run_cleanup(self):
        """
        Runs the cleanup of OpenStack provider
        """
        ci_instances = self.get_active_circle_ci_instances()
        print("Found {} active instances using CircleCI keys...".format(len(ci_instances)))

        for instance in ci_instances:
            print("Checking instance {}...".format(instance.name))
            print("  > id={}, key_name={}, created={}".format(
                instance.id,
                instance.key_name,
                instance.created
            ))
            # Double-check to make sure that the instance is using the circleci keypair.
            if instance.key_pair != 'circleci':
                print("  > SKIPPING: Instance keypair name {} != 'circleci'!".format(
                    instance.key_pair
                ))
                continue

            # Check if it's a valid date
            try:
                instance_age = datetime.strptime(
                    instance.created,
                    '%Y-%m-%dT%H:%M:%SZ'
                )
            except ValueError:
                instance_age = None

            if instance_age and instance_age < self.age_limit:
                print("  > TERMINATING instance (age: {} seconds, age threshold: {} seconds)...".format(
                    instance_age,
                    self.age_limit
                ))
                if not self.dry_run:
                    instance.delete()
                    # TODO: Append deleted ips
                    # instance.accessIPv4 doesn't have any IP's
                    # self.cleaned_ips.append()
            else:
                print("  > SKIPPING: Instance is only {} seconds old (age threshold is {} seconds).".format(
                    instance_age,
                    self.age_limit
                ))

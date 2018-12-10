from collections import namedtuple
from datetime import datetime
from novaclient import client
import pytz


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
        self.cleaned_ips = namedtuple('CleanedServerIps', ['IPv4', 'IPv6'])
        self.cleaned_ips.IPv4 = []
        self.cleaned_ips.IPv6 = []
        self.active_servers = namedtuple('ActiveServerIps', ['IPv4', 'IPv6'])
        self.cleaned_ips.IPv4 = []
        self.cleaned_ips.IPv6 = []


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

        Note: key_name parameter is useless if ran with a user that is not an
              admin. It's good to check twice somewhere else.
        """
        server_list = self.nova.servers.list(
            search_opts={
                'key_name': 'circleci'
            }
        )
        # Filter any keys that are not from circleci in case our query
        # was ignored
        server_list = [s for s in server_list if s.key_name == 'circleci']
        return server_list

    def get_server_ips(self, server_id):
        """
        Returns IP's associated with the server from OpenStack provider
        """
        server_ips = namedtuple('ServerIps', ['IPv4', 'IPv6'])
        server_ips.IPv4 = []
        server_ips.IPv6 = []

        # Adds all IP addresses related to that instance to list
        ips = self.nova.servers.ips(server_id)
        for address in ips.get('Ext-Net', []):
            if address['version'] == 4:
                server_ips.IPv4.append(address['addr'])
            else:
                server_ips.IPv6.append(address['addr'])

        return server_ips

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
            if instance.key_name != 'circleci':
                print("  > SKIPPING: Instance keypair name {} != 'circleci'!".format(
                    instance.key_name
                ))
                continue

            # Check if it's a valid date and add UTC timezone
            try:
                instance_age_unaware = datetime.strptime(
                    instance.created,
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                instance_age = instance_age_unaware.replace(tzinfo=pytz.UTC)
            except ValueError:
                instance_age = None

            # If instance is older than age limit
            if instance_age and instance_age < self.age_limit:
                # Saves instance related IP's (both IPv4 and IPv6) so we
                # can erase them later from the DNS without guessing
                instance_ips = self.get_server_ips(instance.id)
                self.cleaned_ips.IPv4 += instance_ips.IPv4
                self.cleaned_ips.IPv6 += instance_ips.IPv6
                print("  > Instance IP's: IPv4={}, IPv6={}".format(
                    instance_ips.IPv4,
                    instance_ips.IPv6
                ))

                # Terminate the servers
                if not self.dry_run:
                    print("  > TERMINATING instance (age: {} seconds, age threshold: {} seconds)...".format(
                        instance_age,
                        self.age_limit
                    ))
                    instance.delete()
                else:
                    print("  > DRY_RUN: TERMINATING instance (age: {} seconds, age threshold: {} seconds)...".format(
                        instance_age,
                        self.age_limit
                    ))
            else:
                # Save active server IP's
                instance_ips = self.get_server_ips(instance.id)
                self.active_servers.IPv4 += instance_ips.IPv4
                self.active_servers.IPv6 += instance_ips.IPv6
                print("  > Instance IP's: IPv4={}, IPv6={}".format(
                    instance_ips.IPv4,
                    instance_ips.IPv6
                ))
                print("  > SKIPPING: Instance is only {} seconds old (age threshold is {} seconds).".format(
                    instance_age,
                    self.age_limit
                ))

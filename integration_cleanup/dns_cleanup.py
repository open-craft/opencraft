import xmlrpc.client


class DnsCleanupInstance:
    """
    Handles the cleanup of dangling DNS entries
    """
    def __init__(self, zone_id, api_key, api_url='https://rpc.gandi.net/xmlrpc/', dry_run=False):
        """
        Set up variables needed for cleanup
        """
        self.api_key = api_key
        self.dry_run = dry_run
        self.zone_id = zone_id

        self.client = xmlrpc.client.ServerProxy(api_url)

    def get_dns_record_list(self):
        """
        Returns list of all DNS entries for the specified zone
        """
        return client.domain.zone.record.list(self.api_key, self.zone_id, 0)

    def run_cleanup(self, ip_addresses):
        """
        Runs Gandi's DNS cleanup using XMLRPC client using their API

        Takes in a namedtuple with a list of IPv4 and IPv6 addresses like this:
        namedtuple('ServerIps', ['IPv4', 'IPv6']).

        Currently we are only using the IPv4 on the DNS entries, so the IPv6
        addresses are being ignored
        """
        records_to_delete = []

        # Get DNS records
        dns_records = self.get_dns_record_list()

        # Find DNS entries related to ip_addresses input
        for record in dns_records:
            if record['value'] in ip_addresses.IPv4:
                records_to_delete.append(record)

        print("Found {} entries related to old instances...".format(len(records_to_delete)))

        # Delete entries
        for record in records_to_delete:
            print("DNS Entry {}...".format(record['id']))
            print("  > Name: {}".format(record['name']))
            print("  > Type: {}".format(record['type']))
            print("  > Value: {}".format(record['value']))

            if not self.dry_run:
                print("  > DELETING DNS entry {} (related to {})...".format(
                    record['name'],
                    record['value']
                ))
                # TODO: Delete instance here
            else:
                print("  > DRY_RUN: DELETING DNS entry {} (related to {})...".format(
                    record['name'],
                    record['value']
                ))

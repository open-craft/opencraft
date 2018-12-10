import xmlrpc.client


BATCH_SIZE = 100


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
        dns_entries = []
        dns_entry_count = self.client.domain.zone.record.count(self.api_key, self.zone_id, 0)

        for page_num in range(int(dns_entry_count/BATCH_SIZE) + 1):
            dns_entries += self.client.domain.zone.record.list(
                self.api_key,
                self.zone_id,
                0,
                {
                    'items_per_page': 200,
                    'page': page_num
                }
            )

        return dns_entries

    def run_cleanup(self, deletion_blacklist=None, cleaned_up_hashes=[]):
        """
        Runs Gandi's DNS cleanup using XMLRPC client using their API

        deletion_blacklist: Takes in a namedtuple with a list of IPv4 and IPv6
        addresses like this: namedtuple('ServerIps', ['IPv4', 'IPv6']).
        This is the list of currently active servers wich the DNS entries
        shouldn't be deleted.

        Currently we are only using the IPv4 on the DNS entries, so the IPv6
        addresses are being ignored
        """
        print("\n --- Starting  Gandi DNS Cleanup ---")
        if self.dry_run:
            print("Running in DRY_RUN mode, no actions will be taken.")

        records_to_delete = []
        hashes_to_clean = cleaned_up_hashes

        # Get DNS records
        dns_records = self.get_dns_record_list()
        print("Found {} DNS entries...".format(len(dns_records)))

        # Add all entries not on deletion_blacklist that contain
        # "integration" and are A records
        skipped_count_blacklist = 0
        skipped_count_not_integration = 0
        for record in dns_records:
            if record['type'] == 'A':
                if deletion_blacklist and record['value'] not in deletion_blacklist.IPv4:
                    if 'integration' in record['name']:
                        # Remove record from DNS list and add to deletion list
                        dns_records.remove(record)
                        records_to_delete.append(record)
                        # Save integration hash to check for cname records
                        hashes_to_clean.append(record['name'].split('.')[1])
                    else:
                        skipped_count_not_integration += 1
                else:
                    skipped_count_blacklist += 1

        if skipped_count_blacklist:
            print("  > Skipped {} A records as they are related to active servers...".format(
                  skipped_count_blacklist
            ))
        if skipped_count_not_integration:
            print("  > Skipped {} A records as they are not related to integration...".format(
                  skipped_count_not_integration
            ))

        # Remove possible duplicates
        hashes_to_clean = list(set(hashes_to_clean))

        # Add all records with hashes of recourses that are marked for deletion
        # or have been marked for deletion
        # This one is not a smart loop, but does the job
        skipped_count = 0
        for record in dns_records:
            if any(hash in record['name'] for hash in hashes_to_clean):
                dns_records.remove(record)
                records_to_delete.append(record)
            else:
                skipped_count += 1

        print("  > Skipped {} records as they are not related to any hash marked for deletion...".format(
              skipped_count
        ))

        print("Found {} entries related to old instances. Starting deletion process...".format(
            len(records_to_delete)
        ))

        # Delete entries
        for record in records_to_delete:
            print("  > DNS Entry {}...".format(record['id']))
            print("    * Name: {}".format(record['name']))
            print("    * Type: {}".format(record['type']))
            print("    * Value: {}".format(record['value']))

            print("    * DELETING DNS entry {} (related to {})...".format(
                record['name'],
                record['value']
            ))
            if not self.dry_run:
                # TODO: Delete instance here
                pass

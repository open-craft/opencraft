#!/edx/bin/python.edxapp
# pylint: skip-file

from configparser import ConfigParser
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import time
import sys


if __name__ == '__main__':

    def hours_to_milliseconds(hours):
        return hours * 60 * 60 * 1000

    client = Elasticsearch()

    # Grab the server_name_prefix passed to this script by the ansible playbook. This will be used as the
    # ConfigParser "section" name for the output data. This is so the data can easily be associated with this app
    # server by the `activity_csv` management command.
    name_prefix = sys.argv[1]

    # Get the number of days going back that we should search ES for
    num_days = int(sys.argv[2])

    # Must use time.time() because it has a more accurate representation of
    # seconds since epoch than datetime.datetime.utcnow().timestamp() (which
    # appears to be about 25000 seconds, or almost 7 hours, behind)
    now = int(time.time() * 1000)

    # Query for the host matching the name_prefix
    # Only query access log data, and ignore heartbeat or xqueue/get_queuelen requests
    base_search = Search(using=client) \
        .query("match", host=name_prefix) \
        .query("match", source="/edx/var/log/nginx/access.log") \
        .exclude("match", request="heartbeat") \
        .exclude("match", request="xqueue/get_queuelen")

    # Aggregate the unique hits by proxy_ip
    base_search.aggs.bucket("unique_hits", "terms", size=10000, field="proxy_ip.keyword")

    unique_ips = set()
    total_hits = 0

    # Start num_days ago, and query for every 6 hour timeframe since
    for start_time in range(now - hours_to_milliseconds(num_days * 24), now, hours_to_milliseconds(6)):
        # Don't search beyond right now
        end_time = min(start_time + hours_to_milliseconds(6), now)

        # Search for the current 6 hour window
        time_filter = {
            "@timestamp": {
                "gte": start_time,
                "lt": end_time,
                "format": "epoch_millis"
            }
        }
        es_search = base_search.filter("range", **time_filter)

        # Python slice syntax is used to set the `from` and `size`
        # parameters for the search, which we want set to 0
        response = es_search[0:0].execute()

        for bucket in response["aggregations"]["unique_hits"]["buckets"]:
            ip = bucket["key"]

            # Ignore requests without a proxy_ip
            if ip == "-":
                continue

            unique_ips.add(ip)
            total_hits += bucket["doc_count"]

    stats = {
        'unique_hits': len(unique_ips),
        'total_hits': total_hits,
    }

    # Build the ConfigParser data.
    config = ConfigParser()
    config.add_section(name_prefix)
    for key, value in stats.items():
        config.set(name_prefix, key, str(value))

    # Output the data in ConfigParser format to stdout and to a file.
    config.write(sys.stdout)
    if len(sys.argv) > 3:
        filename = sys.argv[3]
        print >> sys.stderr, 'Writing to file passed via parameter: {filename}'.format(filename=filename)
        with open(filename, 'w') as output_file:
            config.write(output_file)

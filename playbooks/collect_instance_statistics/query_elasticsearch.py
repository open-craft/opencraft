#!/edx/bin/python.edxapp
# pylint: skip-file

from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime, timezone, timedelta
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import sys


def valid_date(s):
    try:
        # Set the tzinfo to `timezone.utc` to be consistent
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


if __name__ == '__main__':

    def hours_to_milliseconds(hours):
        return hours * 60 * 60 * 1000

    parser = ArgumentParser()
    parser.add_argument(
        '--name-prefix',
        default=None,
        help='The fully qualified domain name to filter results by',
        required=True
    )
    parser.add_argument(
        '--from',
        dest='from_date',
        default=None,
        type=valid_date,
        help='The first day on which statistics should be gathered.',
        required=True
    )
    parser.add_argument(
        '--to',
        dest='to_date',
        default=None,
        type=valid_date,
        help='The last day on which statistics should be gathered.',
        required=True
    )
    parser.add_argument(
        '--out',
        default=None,
        help='Path to the output file of the new CSV. Leave blank to use stdout.'
    )
    args = parser.parse_args()

    # datetime.timestamp() returns the value in seconds
    start_timestamp_ms = int(args.from_date.timestamp() * 1000)

    # The MS timestamp for the end date is 1 day later, minus 1 millisecond
    end_timestamp_ms = int((args.to_date + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)

    client = Elasticsearch()

    # Query for the host matching the name_prefix
    # Only query access log data, and ignore heartbeat or xqueue/get_queuelen requests
    base_search = Search(using=client) \
        .query("match_phrase", host=args.name_prefix) \
        .query("match_phrase", source="/edx/var/log/nginx/access.log") \
        .exclude("match_phrase", request="heartbeat") \
        .exclude("match_phrase", request="xqueue/get_queuelen")

    # Aggregate the unique hits by proxy_ip
    base_search.aggs.bucket("unique_hits", "terms", size=10000, field="proxy_ip.keyword")

    unique_ips = set()
    total_hits = 0

    # Start num_days ago, and query for every 6 hour timeframe since
    for start_time in range(start_timestamp_ms, end_timestamp_ms, hours_to_milliseconds(6)):
        # Don't search beyond right end_timestamp_ms
        end_time = min(start_time + hours_to_milliseconds(6), end_timestamp_ms)

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
    config.add_section(args.name_prefix)
    for key, value in stats.items():
        config.set(args.name_prefix, key, str(value))

    # Output the data in ConfigParser format to stdout and to a file.
    config.write(sys.stdout)
    if args.out:
        print('Writing to file passed via parameter: {filename}'.format(filename=args.out), sys.stderr)
        with open(args.out, 'w') as output_file:
            config.write(output_file)

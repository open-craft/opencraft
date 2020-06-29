#!/home/ubuntu/instance_statistics_venv/bin/python
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
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


if __name__ == '__main__':

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

    client = Elasticsearch()

    unique_ips = set()
    total_hits = 0

    # Start at from_date and go until to_date, incrementing by 1 day
    # (at the end of the loop)
    date = args.from_date
    while date <= args.to_date:
        es_index = 'filebeat-{date}'.format(date=date.strftime("%Y.%m.%d"))

        # Query for the host matching the name_prefix
        # Only query access log data, and ignore heartbeat or xqueue/get_queuelen requests
        search = Search(using=client, index=es_index) \
            .query("match_phrase", host=args.name_prefix) \
            .query("match_phrase", source="/edx/var/log/nginx/access.log") \
            .exclude("match_phrase", request="heartbeat") \
            .exclude("match_phrase", request="xqueue/get_queuelen")

        # Aggregate the unique hits by proxy_ip
        search.aggs.bucket("unique_hits", "terms", size=10000, field="proxy_ip.keyword")

        # Python slice syntax is used to set the `from` and `size`
        # parameters for the search, which we want set to 0
        response = search[0:0].execute()

        for bucket in response["aggregations"]["unique_hits"]["buckets"]:
            ip = bucket["key"]

            # Ignore requests without a proxy_ip
            if ip == "-":
                continue

            unique_ips.add(ip)
            total_hits += bucket["doc_count"]

        date += timedelta(days=1)

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

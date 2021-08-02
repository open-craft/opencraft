#!/usr/bin/env python3
# pylint: skip-file

from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import sys

from six.moves.configparser import ConfigParser


def valid_date(s):
    """
    Verify that the string passed in is a date
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument(
        '--name-prefixes',
        default=None,
        help='Comma-separated name prefixes to filter results by. Each will be run sequentially',
        required=True
    )
    parser.add_argument(
        '--start-date',
        default=None,
        type=valid_date,
        help='The first day on which statistics should be gathered. FORMAT: YYYY-MM-DD',
        required=True
    )
    parser.add_argument(
        '--end-date',
        default=None,
        type=valid_date,
        help='The last day on which statistics should be gathered.',
        required=True
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Elasticsearch API host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9200,
        help='Elasticsearch API port'
    )
    parser.add_argument(
        '--use-ssl',
        action='store_true',
        default=False,
        help='Use SSL to connect to Elasticsearch API'
    )
    parser.add_argument(
        '--ca-certs',
        default=None,
        help='Path to the Elasticsearch CA certificate file'
    )
    parser.add_argument(
        '--username',
        default=None,
        help='Elasticsearch API username'
    )
    parser.add_argument(
        '--password',
        default=None,
        help='Elasticsearch API password'
    )
    parser.add_argument(
        '--out',
        default=None,
        help='Path to the output file of the new CSV. Leave blank to use stdout.'
    )
    args = parser.parse_args()

    client = Elasticsearch(
        host=args.host,
        port=args.port,
        use_ssl=args.use_ssl,
        ca_certs=args.ca_certs,
        http_auth=(args.username, args.password,)
    )
    config = ConfigParser()

    name_prefixes = args.name_prefixes.split(',')

    for name_prefix in name_prefixes:

        unique_ips = set()
        total_hits = 0

        # Start at start_date and go until end_date, incrementing by 1 day
        # (at the end of the loop)
        date = args.start_date
        while date <= args.end_date:
            es_index = 'filebeat-{date}'.format(date=date.strftime("%Y.%m.%d"))

            # Query for the host matching the name_prefix
            # Only query access log data, and ignore heartbeat or xqueue/get_queuelen requests
            search = Search(using=client, index=es_index) \
                .query("match_phrase", host=name_prefix) \
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

        # Build the ConfigParser data
        config.add_section(name_prefix)
        for key, value in stats.items():
            config.set(name_prefix, key, str(value))

    # Output the data in ConfigParser format to stdout and to a file.
    config.write(sys.stdout)
    if args.out:
        print('Writing to file passed via parameter: {filename}'.format(filename=args.out), file=sys.stderr)
        with open(args.out, 'w') as output_file:
            config.write(output_file)

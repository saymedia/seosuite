 # -*- coding: utf-8 -*-

# usage:
# > python seoreporter.py [type] [format] [run_id]
# example:
# > python seoreporter.py build junit d09b8571-5c8a-42ff-8ab7-c38f4f8871c4

import optparse
import os

import MySQLdb
import yaml

import seoreporter

def run(options):
    if options.database:
        with open(options.database, 'r') as f:
            env = yaml.load(f)
        db_conf = env.get('db', {})
    else:
        db_conf = {
            'host': os.environ.get('SEO_DB_HOSTNAME'),
            'user': os.environ.get('SEO_DB_USERNAME'),
            'pass': os.environ.get('SEO_DB_PASSWORD'),
            'name': os.environ.get('SEO_DB_DATABASE'),
        }

    # Initialize the database cursor
    db = MySQLdb.connect(host=db_conf.get('host'), user=db_conf.get('user'),
        passwd=db_conf.get('pass'), db=db_conf.get('name'), use_unicode=True)

    if options.run_id:
        run_id = options.run_id
    else:
        # get the latest run_id
        run_id = seoreporter.fetch_latest_run_id(db)

    if options.output:
        with open(options.output, 'w') as f:
            f.write(seoreporter.report(db, options.type, options.format, run_id))
    else:
        print seoreporter.report(db, options.type, options.format, run_id)

if __name__ == "__main__":
    parser = optparse.OptionParser(description='Runs various reports on the seocrawler database in various formats.')

    parser.add_option('-r', '--run_id', type="string", default=None,
        help='The id from a previous run to resume. Defaults to latest run_id.')
    parser.add_option('-t', '--type', type="string", default='build',
        help='The type of report to run.')
    parser.add_option('-f', '--format', type="string", default='junit',
        help='The type of format to output.')

    parser.add_option('--database', type="string",
        help='A yaml configuration file with the database configuration properties.')


    parser.add_option('-o', '--output', type="string",
        help='The path of the file where the output junix xml will be written to.')

    args = parser.parse_args()[0]

    run(args)

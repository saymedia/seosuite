import yaml
import argparse
import json
import os

import MySQLdb

from seocrawler import crawl
from seoreporter import report


def run(options):

    if options.database:
        env = yaml.load(options.database)
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
        passwd=db_conf.get('pass'), db=db_conf.get('name'))

    urls = []
    url_associations = {}
    processed_urls = {}
    run_id = None
    if options.file:
        urls = [url.strip() for url in options.file.readlines()]
    elif options.base_url:
        urls = [options.base_url,]
    elif options.yaml:
        url_yaml = yaml.load(options.yaml)
        urls = url_yaml.get('seocrawlerurls', [])
    elif options.run_id:
        cur = db.cursor()
        cur.execute('SELECT * FROM crawl_save WHERE run_id = %s',
            (options.run_id,))
        run = cur.fetchone()
        if not run:
            raise Exception('No instance found matching the supplied run_id.')

        urls = json.loads(run[2])
        url_associations = json.loads(run[3])
        run_id = options.run_id

        cur.execute('SELECT id, address FROM crawl_urls WHERE run_id = %s',
            (options.run_id,))
        processed_urls = dict([(row[1], row[0]) for row in cur.fetchall()])

    run_id = crawl(urls, db, options.internal, options.delay,
        options.user_agent, url_associations, run_id, processed_urls)

    if options.output:
        options.output.write(report(db, 'build', 'junit', run_id))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl the given url(s) and check them for SEO or navigation problems.')

    # Input sources
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('-f', '--file', type=file,
        help='A file containing a list of urls (one url per line) to process.')
    inputs.add_argument('-u', '--base_url', type=str,
        help='A single url to use as a starting point for crawling.')
    inputs.add_argument('-r', '--run_id', type=str,
        help='The id from a previous run to resume.')
    inputs.add_argument('-y', '--yaml', type=file,
        help='A yaml file containing a list of urls to process. The yaml file should have a section labeled "seocrawlerurls" that contains a list of the urls to crawl.')

    # Processing options
    parser.add_argument('-i', '--internal', action="store_true",
        help='Crawl any internal link urls that are found in the content of the page.')
    parser.add_argument('--user-agent', type=str, default='Twitterbot/1.0 (SEO Crawler)',
        help='The user-agent string to request pages with.')
    parser.add_argument('--delay', type=int, default=0,
        help='The number of milliseconds to delay between each request.')

    parser.add_argument('--database', type=file,
        help='A yaml configuration file with the database configuration properties.')


    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
        help='The path of the file where the output junix xml will be written to.')

    args = parser.parse_args()

    run(args)
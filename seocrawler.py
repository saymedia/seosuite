import yaml
import argparse

import MySQLdb

from seocrawler import crawl


def run(options):

    env = yaml.load(open('config.yaml'))

    # Initialize the database cursor
    db_conf = env.get('db', {})
    db = MySQLdb.connect(host=db_conf.get('host'), user=db_conf.get('user'),
        passwd=db_conf.get('pass'), db=db_conf.get('name'))

    urls = []
    if options.file:
        urls = [url.strip() for url in options.file.readlines()]
    elif options.base_url:
        urls = [options.base_url,]

    crawl(urls, db, options.internal, options.delay, options.user_agent)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl the given url(s) and check them for SEO or navigation problems.')

    # Input sources
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('-f', '--file', type=file,
        help='A file containing a list of urls (one url per line) to process.')
    inputs.add_argument('-u', '--base_url', type=str,
        help='A single url to use as a starting point for crawling.')

    # Processing options
    parser.add_argument('-i', '--internal', type=bool, default=False,
        help='Crawl any internal link urls that are found in the content of the page.')
    parser.add_argument('--user-agent', type=str, default='Twitterbot/1.0',
        help='The user-agent string to request pages with.')
    parser.add_argument('--delay', type=int, default=0,
        help='The number of milliseconds to delay between each request.')

    
    args = parser.parse_args()

    run(args)
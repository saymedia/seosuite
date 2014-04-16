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
        raise NotImplementedError('Starting from a base_url is not yet supported.')
    elif options.run_id:
        raise NotImplementedError('Restarting an existing run_id is not yet supported.')

    crawl(urls, options.internal)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl the given url(s) and check them for SEO or navigation problems.')

    # Input sources
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('-f', '--file', type=file,
        help='A file containing a list of urls (one url per line) to process.')
    inputs.add_argument('-u', '--base_url', type=str,
        help='A single url to use as a starting point for crawling.')
    inputs.add_argument('-r', '--run_id', type=str,
        help='The id of a previous crawler execution.')

    # Processing options
    parser.add_argument('-i', '--internal', type=bool, default=False,
        help='Crawl any internal link urls that are found in the content of the page.')

    
    args = parser.parse_args()

    run(args)
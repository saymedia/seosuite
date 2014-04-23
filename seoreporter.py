 # -*- coding: utf-8 -*-

# usage:
# > python seoreporter.py [type] [format] [run_id]
# example:
# > python seoreporter.py build junit d09b8571-5c8a-42ff-8ab7-c38f4f8871c4

import optparse
import os
import datetime

import MySQLdb
import yaml

import gdata.spreadsheet.service
import gdata.service
import gdata.spreadsheet
import gdata.docs
import gdata.docs.client
import gdata.docs.data

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

    # Optionally upload to google docs
    gd_client = None
    if options.upload:
        def gd_login(email, password):
            client = gdata.docs.client.DocsClient(source="Recluse SEO Suite")
            client.api_version = "3"
            client.ssl = True
            # pp.pprint(vars(client))
            client.ClientLogin(email, password, client.source)
            return client

        def gd_upload(report, title, client, filename='tmp.xls'):
            with open(filename, 'w') as f:
                f.write(report)
            # print vars(gdata.docs)
            newResource = gdata.docs.data.Resource(filename, title)
            media = gdata.data.MediaSource()
            if options.format == 'xls':
                media.SetFileHandle(filename, 'application/vnd.ms-excel')
                # media.SetFileHandle(filename, 'application/vnd.google-apps.spreadsheet')
            elif options.format == 'csv':
                media.SetFileHandle(filename, 'text/csv')
            newDocument = client.CreateResource(newResource, create_uri=gdata.docs.client.RESOURCE_UPLOAD_URI, media=media)
            return newDocument

        with open(options.database, 'r') as f:
            login = yaml.load(f).get('gdata', {})
        gd_client = gd_login(login.get('user', None), login.get('pass', None))
        if not gd_client:
            raise Exception('Cannot connect to Google Docs.')

        entry = gd_upload(
            seoreporter.report(db, options.type, options.format, run_id),
            'seoreporter - %s - %s' % (options.type, datetime.datetime.today().strftime('dd/mm/yy')),
            gd_client,
            options.output
            )
        print "Uploaded to Google Docs. URL is:"
        print entry.GetAlternateLink().href

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
    parser.add_option('-u', '--upload', action="store_true", default=False,
        help='Upload the file to Google Docs.')


    parser.add_option('-o', '--output', type="string",
        help='The path of the file where the output junix xml will be written to.')

    args = parser.parse_args()[0]

    run(args)

 # -*- coding: utf-8 -*-

# usage:
# > python seoreporter/__init__.py [type] [format] [run_id]
# example:
# > python seoreporter/__init__.py build junit d09b8571-5c8a-42ff-8ab7-c38f4f8871c4

# todo
# output valid jUnit XML output
# output html files in a folder
# output html pages that show the data
# output json

import yaml
import datetime

import MySQLdb

report_types = ('build', 'editorial')
report_formats = ('junit', 'html')


def build_report(db, run_id):
    output = []

    c = db.cursor()

    urls = fetch_run(db, run_id)

    # 500 errors
    # TODO add other error codes
    c.execute('''SELECT address, status_code FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND (status_code LIKE %s OR status_code = 0)
        ORDER BY timestamp ASC''', (run_id, '5%',))
    results = c.fetchall()
    output.append({
        'name': '5xx or 0 status codes',
        'values': [result[0] for result in results],
        })

    # 404s
    c.execute('''SELECT address, status_code FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND status_code LIKE %s
        ORDER BY timestamp ASC''', (run_id, '4%',))
    results = c.fetchall()
    output.append({
        'name': '4xx status codes',
        'values': [result[0] for result in results],
        })

    # missing canonicals
    c.execute('''SELECT address FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND canonical IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'missing canonical',
        'values': [result[0] for result in results],
        })

    # missing titles
    c.execute('''SELECT address FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND title_1 IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'missing title',
        'values': [result[0] for result in results],
        })

    # missing meta descriptions
    c.execute('''SELECT address FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND meta_description_1 IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'missing meta_description',
        'values': [result[0] for result in results],
        })

    # lint level critical
    c.execute('''SELECT address, lint_critical FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND lint_critical > 0
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'lint level critical',
        'values': [result[0] + ', ' + result[1] for result in results],
        })

    # lint level error
    c.execute('''SELECT address, lint_error FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND lint_error > 0
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'lint level error',
        'values': [result[0] + ', ' + result[1] for result in results],
        })

    return output


# junit schema:
# https://svn.jenkins-ci.org/trunk/hudson/dtkit/dtkit-format/dtkit-junit-model\
# /src/main/resources/com/thalesgroup/dtkit/junit/model/xsd/junit-4.xsd
def junit_format(report_type, tests, run_id):
    output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    output += '''<testsuite
        name="seoreporter-%s"
        tests="%s"
        timestamp="%s"
        time=""
        errors="%s"
        failures=""
        id="%s"
        package="seoreporter"
        skipped="0">\n''' % (
        report_type,
        len(tests),
        datetime.datetime.utcnow(),
        sum([len(test['values']) for test in tests if 'values' in test and test['values'] > 0]),
        run_id
        )

    for test in tests:
        output += '\t<testcase name="%s">\n' % (test['name'])
        if test['values'] and len(test['values']) > 0:
            # put everything in one element because jenkins ignores > 1
            output += '\t\t<error type="addresses">%s</failure>\n' % (str(test['values']))
        output += '\t</testcase>\n'

    output += '</testsuite>'

    return output


def report(db, report_type, report_format, run_id):
    report_data = None

    if report_type == 'build':
        report_data = build_report(db, run_id)

    if report_data and report_format == 'junit':
        return junit_format(report_type, report_data, run_id)


def fetch_run(db, run_id):
    c = db.cursor()
    c.execute('SELECT * FROM crawl_urls WHERE run_id = %s ORDER BY timestamp DESC', [run_id])
    return c.fetchall()


def fetch_latest_run_id(db):
    run_id = None
    c = db.cursor()
    c.execute('SELECT run_id FROM crawl_urls ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    if result:
        run_id = result[0]
    return run_id


def run():

    env = yaml.load(open('config.yaml'))

    # Initialize the database cursor
    db_conf = env.get('db', {})
    db = MySQLdb.connect(host=db_conf.get('host'), user=db_conf.get('user'),
        passwd=db_conf.get('pass'), db=db_conf.get('name'), use_unicode=True)

    # get the latest run_id
    run_id = fetch_latest_run_id(db)

    print report(db, 'build', 'junit', run_id)

if __name__ == "__main__":
    run()

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

report_types = ('build', 'all')
report_formats = ('junit', 'csv', 'sql')


def all_report(db, run_id):
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute('SELECT * FROM crawl_urls WHERE run_id = %s ORDER BY timestamp DESC', [run_id])
    return c.fetchall()


def build_report(db, run_id):
    output = []

    # c = db.cursor()
    c = db.cursor(MySQLdb.cursors.DictCursor)

    # 500 errors
    # TODO add other error codes
    c.execute('''SELECT address, status_code, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND (status_code LIKE %s OR status_code = 0)
        ORDER BY timestamp ASC''', (run_id, '5%',))
    results = c.fetchall()
    output.append({
        'name': '5xx or 0 status codes',
        'values': [result['address'] + ', ' + str(result['status_code']) for result in results],
        })

    # 404s
    c.execute('''SELECT address, status_code, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND status_code LIKE %s
        ORDER BY timestamp ASC''', (run_id, '4%',))
    results = c.fetchall()
    output.append({
        'name': '4xx status codes',
        'values': [result['address'] + ', ' + str(result['status_code']) for result in results],
        })

    # missing canonicals
    c.execute('''SELECT address, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND canonical IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'missing canonical',
        'values': [result['address'] + ', ' + str(result['timestamp']) for result in results],
        })

    # missing titles
    c.execute('''SELECT address, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND title_1 IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'missing title',
        'values': [result['address'] + ', ' + str(result['timestamp']) for result in results],
        })

    # missing meta descriptions
    c.execute('''SELECT address, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND meta_description_1 IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'missing meta_description',
        'values': [result['address'] + ', ' + str(result['timestamp']) for result in results],
        })

    # lint level critical
    c.execute('''SELECT address, timestamp, lint_critical FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND lint_critical > 0
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'lint level critical',
        'values': [result['address'] + ', ' + str(result['timestamp']) + ', ' + str(result['lint_critical']) for result in results],
        })

    # lint level error
    c.execute('''SELECT address, timestamp, lint_error FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND lint_error > 0
        ORDER BY timestamp ASC''', (run_id,))
    results = c.fetchall()
    output.append({
        'name': 'lint level error',
        'values': [result['address'] + ', ' + str(result['timestamp']) + ', ' + str(result['lint_error']) for result in results],
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


def xsl_format(report_type, tests, run_id):
    output = '''<?xml version="1.0"?>
    <Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
     xmlns:o="urn:schemas-microsoft-com:office:office"
     xmlns:x="urn:schemas-microsoft-com:office:excel"
     xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
     xmlns:html="http://www.w3.org/TR/REC-html40">
     <Worksheet ss:Name="%s">
      <Table ss:ExpandedColumnCount="3" x:FullColumns="1" x:FullRows="1">
       <Row>
        <Cell><Data ss:Type="String">Run Id</Data></Cell>
        <Cell><Data ss:Type="String">Name</Data></Cell>
        <Cell><Data ss:Type="String">Value</Data></Cell>
       </Row>''' % (report_type)

    for test in tests:
        if test['values'] and len(test['values']) > 0:
            for value in test['values']:
                output += '''
        <Row>
          <Cell><Data ss:Type="String">%s</Data></Cell>
          <Cell><Data ss:Type="String">%s</Data></Cell>
          <Cell><Data ss:Type="String">%s</Data></Cell>
        </Row>
                ''' % (run_id, test['name'], value)
        else:
            output += '''
        <Row>
          <Cell><Data ss:Type="String">%s</Data></Cell>
          <Cell><Data ss:Type="String">%s</Data></Cell>
        </Row>
            ''' % (run_id, test['name'])

    output += '''
      </Table>
     </Worksheet>
    </Workbook>'''

    return output


def csv_format(report_type, tests, run_id):
    output = "run_id,name,value,timestamp,count"

    for test in tests:
        if test['values'] and len(test['values']) > 0:
            for value in test['values']:
                output += "\n%s,%s,%s" % (run_id, test['name'], value)
        else:
            output += "\n%s,%s" % (run_id, test['name'])

    return output


def sql_format(report_type, tests, run_id):
    output = '''
DROP TABLE IF EXISTS `seoreport`;
CREATE TABLE `seoreport` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `report_type` varchar(2048) NOT NULL DEFAULT '',
  `name` varchar(2048) NOT NULL DEFAULT '',
  `value` varchar(2048) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    '''

    for test in tests:
        if test['values'] and len(test['values']) > 0:
            for value in test['values']:
                output += "INSERT INTO `seoreport` VALUES (NULL, '%s', '%s', '%s', '%s', NULL);\n" % (run_id, report_type, test['name'], value.replace('\'', '\\\''))
        else:
            output += "INSERT INTO `seoreport` VALUES (NULL, '%s', '%s', '%s', NULL, NULL);\n" % (run_id, report_type, test['name'])

    return output


def report(db, report_type, report_format, run_id):
    report_data = None

    if report_type == 'build':
        report_data = build_report(db, run_id)

    if report_type == 'all':
        report_data = build_report(db, run_id)

    if report_data and report_format == 'junit':
        return junit_format(report_type, report_data, run_id)

    if report_data and report_format == 'csv':
        return csv_format(report_type, report_data, run_id)

    if report_data and report_format == 'xsl':
        return xsl_format(report_type, report_data, run_id)

    if report_data and report_format == 'sql':
        return sql_format(report_type, report_data, run_id)


def fetch_latest_run_id(db):
    run_id = None
    c = db.cursor()
    c.execute('SELECT run_id FROM crawl_urls ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    if result:
        run_id = result[0]
    return run_id


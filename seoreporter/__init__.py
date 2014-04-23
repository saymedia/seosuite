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
import time
import datetime

import MySQLdb

start = None

def report(db, report_type, report_format, run_id):
    global start
    report_data = []
    start = time.time()
    # print [report_type, report_format, run_id]

    if report_type == 'build':
        report_data = build_report(db, run_id)
    elif report_type == 'status_code':
        report_data = status_code_report(db, run_id)
    elif report_type == 'all':
        report_data = build_report(db, run_id)
    else:
        raise Exception('Report type not supported')

    if report_format == 'junit':
        return junit_format(report_type, report_data, run_id)
    elif report_format == 'csv':
        return csv_format(report_type, report_data, run_id)
    elif report_format == 'xls':
        return xls_format(report_type, report_data, run_id)
    elif report_format == 'sql':
        return sql_format(report_type, report_data, run_id)
    else:
        raise Exception('Report format not supported')


def fetch_latest_run_id(db):
    run_id = None
    c = db.cursor()
    c.execute('SELECT run_id FROM crawl_urls ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    if result:
        run_id = result[0]
    return run_id


def all_report(db, run_id):
    c = db.cursor(MySQLdb.cursors.DictCursor)
    c.execute('''SELECT
        id, run_id, level, content_hash, address, domain, path, external,
        status_code, status, body, size, address_length, encoding, content_type,
        response_time, redirect_uri, canonical, title_1, title_length_1,
        title_occurences_1, meta_description_1, meta_description_length_1,
        meta_description_occurrences_1, h1_1, h1_length_1, h1_2, h1_length_2,
        h1_count, meta_robots, rel_next, rel_prev, lint_critical, lint_error,
        lint_warn, lint_info, lint_results, timestamp
        FROM crawl_urls WHERE run_id = %s ORDER BY timestamp DESC''', [run_id])
    return [{
        'name': 'all',
        'fields': [
            'id', 'run_id', 'level', 'content_hash', 'address', 'domain', 'path', 'external',
            'status_code', 'status', 'body', 'size', 'address_length', 'encoding', 'content_type',
            'response_time', 'redirect_uri', 'canonical', 'title_1', 'title_length_1',
            'title_occurences_1', 'meta_description_1', 'meta_description_length_1',
            'meta_description_occurrences_1', 'h1_1', 'h1_length_1', 'h1_2', 'h1_length_2',
            'h1_count', 'meta_robots', 'rel_next', 'rel_prev', 'lint_critical', 'lint_error',
            'lint_warn', 'lint_info', 'lint_results', 'timestamp',
            ],
        'values': c.fetchall(),
        }]


def status_code_report(db, run_id):
    output = []

    # c = db.cursor()
    c = db.cursor(MySQLdb.cursors.DictCursor)

    # 500 errors
    # TODO add other error codes
    c.execute('''SELECT address, timestamp, status_code FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND (status_code LIKE %s OR status_code = 0)
        ORDER BY timestamp ASC''', (run_id, '5%',))
    output.append({
        'name': '5xx or 0 status codes',
        'fields': ['address', 'timestamp', 'status_code'],
        'values': c.fetchall(),
        })

    # 404s
    c.execute('''SELECT address, timestamp, status_code FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND status_code LIKE %s
        ORDER BY timestamp ASC''', (run_id, '4%',))
    output.append({
        'name': '4xx status codes',
        'fields': ['address', 'timestamp', 'status_code'],
        'values': c.fetchall(),
        })

    return output


def build_report(db, run_id):
    output = []

    # c = db.cursor()
    c = db.cursor(MySQLdb.cursors.DictCursor)

    # 500 errors
    # TODO add other error codes
    c.execute('''SELECT address, timestamp, status_code FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND (status_code LIKE %s OR status_code = 0)
        ORDER BY timestamp ASC''', (run_id, '5%',))
    output.append({
        'name': '5xx or 0 status codes',
        'fields': ['address', 'timestamp', 'status_code'],
        'values': c.fetchall(),
        })

    # 404s
    c.execute('''SELECT address, timestamp, status_code FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND status_code LIKE %s
        ORDER BY timestamp ASC''', (run_id, '4%',))
    output.append({
        'name': '4xx status codes',
        'fields': ['address', 'timestamp', 'status_code'],
        'values': c.fetchall(),
        })

    # missing canonicals
    c.execute('''SELECT address, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND content_type = 'text/html' AND canonical IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    output.append({
        'name': 'missing canonical',
        'fields': ['address', 'timestamp'],
        'values': c.fetchall(),
        })

    # missing titles
    c.execute('''SELECT address, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND content_type = 'text/html' AND title_1 IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    output.append({
        'name': 'missing title',
        'fields': ['address', 'timestamp'],
        'values': c.fetchall(),
        })

    # missing meta descriptions
    c.execute('''SELECT address, timestamp FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND content_type = 'text/html' AND meta_description_1 IS NULL
        ORDER BY timestamp ASC''', (run_id,))
    output.append({
        'name': 'missing meta_description',
        'fields': ['address', 'timestamp'],
        'values': c.fetchall(),
        })

    # lint level critical
    c.execute('''SELECT address, timestamp, lint_critical FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND lint_critical > 0
        ORDER BY timestamp ASC''', (run_id,))
    output.append({
        'name': 'lint level critical',
        'fields': ['address', 'timestamp', 'lint_critical'],
        'values': c.fetchall(),
        })

    # lint level error
    c.execute('''SELECT address, timestamp, lint_error FROM crawl_urls
        WHERE run_id = %s AND external = 0 AND lint_error > 0
        ORDER BY timestamp ASC''', (run_id,))
    output.append({
        'name': 'lint level error',
        'fields': ['address', 'timestamp', 'lint_error'],
        'values': c.fetchall(),
        })

    return output


# junit schema:
# https://svn.jenkins-ci.org/trunk/hudson/dtkit/dtkit-format/dtkit-junit-model\
# /src/main/resources/com/thalesgroup/dtkit/junit/model/xsd/junit-4.xsd
def junit_format(report_type, tests, run_id):
    global start
    errors = 0
    output = ''

    def junit_row(values):
        o = ''
        for v in values:
            o += '\t\t<error type="addresses">%s</error>\n' % str(v['address'])
        return o

    def junit_row_flat(values):
        o = ''
        # for v in values:
        o += '\t\t<error type="addresses">%s</error>\n' % (", ".join([v['address'] for v in values]))
        return o

    for test in tests:
        # header
        output += '\t<testcase name="%s">\n' % (test['name'])
        # values
        if test['values'] and len(test['values']) > 0:
            errors += len(test['values'])
            # put everything in one element because jenkins ignores > 1
            output += junit_row_flat(test['values'])
        # footer
        output += '\t</testcase>\n'

    header = '''<?xml version="1.0" encoding="UTF-8"?>
    <testsuite
        name="seoreporter-%s"
        tests="%s"
        timestamp="%s"
        time="%s"
        errors="%s"
        failures=""
        id="%s"
        package="seoreporter"
        skipped="0">\n''' % (
        report_type,
        len(tests),
        datetime.datetime.utcnow(),
        time.time() - start,
        errors,
        run_id
        )
    return header + output + '</testsuite>'


def xls_format(report_type, tests, run_id):
    output = '''<?xml version="1.0"?>
    <Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
     xmlns:o="urn:schemas-microsoft-com:office:office"
     xmlns:x="urn:schemas-microsoft-com:office:excel"
     xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
     xmlns:html="http://www.w3.org/TR/REC-html40">
     <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">
      <Version>14.0</Version>
     </DocumentProperties>
     <OfficeDocumentSettings xmlns="urn:schemas-microsoft-com:office:office">
      <AllowPNG/>
     </OfficeDocumentSettings>
     <ExcelWorkbook xmlns="urn:schemas-microsoft-com:office:excel">
      <WindowHeight>6240</WindowHeight>
      <WindowWidth>10000</WindowWidth>
      <WindowTopX>120</WindowTopX>
      <WindowTopY>140</WindowTopY>
      <ProtectStructure>False</ProtectStructure>
      <ProtectWindows>False</ProtectWindows>
     </ExcelWorkbook>
     <Styles>
      <Style ss:ID="Default" ss:Name="Normal">
       <Alignment ss:Vertical="Bottom"/>
       <Borders/>
       <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="12" ss:Color="#000000"/>
       <Interior/>
       <NumberFormat/>
       <Protection/>
      </Style>
     </Styles>'''

    def xls_row(values):
        o = '          <Row>\n'
        for v in values:
            o += '           <Cell>\n            <Data ss:Type="String">' + str(v) + '</Data>\n           </Cell>\n'
        return o + '          </Row>\n'

    for test in tests:
        if test['values'] and len(test['values']) > 0:
            # header
            output += '\n        <Worksheet ss:Name="%s"><Table ss:ExpandedColumnCount="%s" x:FullColumns="1" x:FullRows="1" ss:DefaultColumnWidth="65" ss:DefaultRowHeight="15">\n' % (test['name'].replace('_', ' ').title(), 2 + len(test['values'][0].keys()))
            output += xls_row(['Run Id'] + [o.replace('_', ' ').title() for o in test['values'][0].keys()])
            # values
            for row in test['values']:
                output += xls_row([run_id] + [str(v) for v in row.values()])
            # footer
            output += '''          </Table>
          <WorksheetOptions xmlns="urn:schemas-microsoft-com:office:excel">
           <PageLayoutZoom>0</PageLayoutZoom>
           <ProtectObjects>False</ProtectObjects>
           <ProtectScenarios>False</ProtectScenarios>
          </WorksheetOptions>
        </Worksheet>'''
    output += '\n</Workbook>'

    return output


def csv_format(report_type, tests, run_id):
    output = ""

    def csv_row(values):
        return ",".join(values) + '\n'

    for test in tests:
        if test['values'] and len(test['values']) > 0:
            # header
            output += csv_row(['Run Id', 'Name'] + [o.replace('_', ' ').title() for o in test['values'][0].keys()])
            # values
            for row in test['values']:
                output += csv_row([run_id, test['name'].replace('_', ' ').title()] + [str(v) for v in row.values()])
    return output


def sql_format(report_type, tests, run_id):
    output = ''
    fields = [] # track all the column names used to build the CREATE TABLE

    def sql_row(values, fields):
        o = "INSERT INTO `seoreport` ("
        # columns
        o += ",".join(["`%s`" % (v) for v in fields])
        o += ") VALUES ("
        # values
        o += ",".join([("'%s'" % (v) if v != 'NULL' else 'NULL') for v in values])
        return o + ');\n'

    for test in tests:
        if test['values'] and len(test['values']) > 0:
            fields += [o for o in test['values'][0].keys()]
            for row in test['values']:
                output += sql_row(
                        [run_id, test['name'].replace('_', ' ').title()] + [MySQLdb.escape_string(str(v)) for v in row.values()],
                        ['run_id', 'report_type'] + [o for o in test['values'][0].keys()]
                        )

    header = '''DROP TABLE IF EXISTS `seoreport`;
CREATE TABLE `seoreport` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `report_type` varchar(36) NOT NULL DEFAULT '',
  '''
    for v in set(fields): # dedupe them
        header += '  `%s` varchar(2048) NOT NULL DEFAULT \'\',\n' % (v)
    header += '''
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;\n\n'''
    return header + output


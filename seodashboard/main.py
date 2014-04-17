# -*- coding: utf-8 -*-

import yaml

import MySQLdb

from flask import Flask, render_template
app = Flask(__name__, template_folder='.')
db = None


def fetch_latest_run_id():
    run_id = None
    c = db.cursor()
    c.execute('SELECT run_id FROM crawl_urls ORDER BY timestamp DESC LIMIT 1')
    result = c.fetchone()
    if result:
        run_id = result[0]
    return run_id


def fetch_run(run_id):
    c = db.cursor()
    c.execute('SELECT * FROM crawl_urls WHERE run_id = %s ORDER BY timestamp ASC', [run_id])
    return c.fetchall()


def cols_to_props(results):
    output = []
    for result in results:
        output.append({
            'id':           result[0],
            'run_id':       result[1],
            'level':        result[2],
            'content_hash': result[3],

            'address':        result[4],
            'domain':         result[5],
            'path':           result[6],
            'external':       result[7],
            'status_code':    result[8],
            'status':         result[9],
            'body':           result[10],
            'size':           result[11],
            'address_length': result[12],
            'encoding':       result[13],
            'content_type':   result[14],
            'response_time':  result[15],
            'redirect_uri':   result[16],

            'canonical':                      result[17],
            'title_1':                        result[18],
            'title_length_1':                 result[19],
            'title_occurences_1':             result[20],
            'meta_description_1':             result[21],
            'meta_description_length_1':      result[22],
            'meta_description_occurrences_1': result[23],
            'h1_1':                           result[24],
            'h1_length_1':                    result[25],
            'h1_2':                           result[26],
            'h1_length_2':                    result[27],
            'h1_count':                       result[28],
            'meta_robots':                    result[29],
            'rel_next':                       result[30],
            'rel_prev':                       result[31],

            'lint_critical': result[32],
            'lint_error':    result[33],
            'lint_warn':     result[34],
            'lint_info':     result[35],
            'lint_results':  result[36],

            'timestamp': result[37],
            })
    return output


@app.route("/")
def hello():
    run_id = fetch_latest_run_id()
    crawl_urls = fetch_run(run_id)
    return render_template('index.html', run_id=run_id, crawl_urls=cols_to_props(crawl_urls),)


if __name__ == "__main__":
    env = yaml.load(open('config.yaml'))

    # Initialize the database cursor
    db_conf = env.get('db', {})
    db = MySQLdb.connect(host=db_conf.get('host'), user=db_conf.get('user'),
        passwd=db_conf.get('pass'), db=db_conf.get('name'), use_unicode=True)

    app.run(debug=True)

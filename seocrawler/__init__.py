import time
import uuid
import requests

import seolinter

def crawl(urls, db, internal=False, delay=0, user_agent=None):

    processed_urls = []
    run_id = uuid.uuid4()

    while len(urls) > 0:
        url = urls.pop(0)
        processed_urls.append(url)
        
        status_code, html, stats = retrieve_url(url, user_agent)
        
        if status_code == 200:

            lint_errors, page_details, additional_urls = process_html(html, url)

            if internal and len(additional_urls) > 0:
                for url in additional_urls:
                    if url not in processed_urls and url not in urls:
                        urls.append(url)

        else:
            # Process the error
            lint_errors = []
            page_details = []
            additional_urls = []

        store_results(db, run_id, stats, lint_errors, page_details,
            additional_urls)

        time.sleep( delay / 1000.0 )


def retrieve_url(url, user_agent=None):

    headers = {}
    if user_agent:
        headers['User-Agent'] = user_agent
        if 'Googlebot' in user_agent:
            # TODO: append ?__escaped_fragment__= to the url
            pass

    try:
        start = time.time()
        res = requests.get(url, headers=headers, timeout=15)
    except Exception, e:
        print e
        # TODO: Properly handle the failure. reraise?
    finally:
        request_time = time.time() - start

    print res.request.headers

    html = res.text
    stats = {
        'result_code': res.status_code,
        'result_message': res.reason,
        'page_size': len(res.text),
        'duration': request_time,
        'encoding': res.encoding,
    }
    
    return res.status_code, html, stats


def process_html(html, url):

    lint_errors = seolinter.lint(html)

    page_details = extract_page_details(html, url)

    additional_urls = extract_internal_urls(html, url)

    return lint_errors, page_details, additional_urls


def extract_internal_urls(html, url):
    return []


def extract_page_details(html, url):
    return {}


def store_results(db, run_id, stats, lint_errors, page_details, additional_urls):
    cur = db.cursor()

    pass
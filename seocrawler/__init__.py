import time
import uuid
import requests
import re
from urlparse import urlparse

import seolinter

def crawl(urls, db, internal=False, delay=0, user_agent=None):

    processed_urls = []
    run_id = uuid.uuid4()

    while len(urls) > 0:
        url = urls.pop(0)

        if is_relative_url(url):
            raise ValueError('A relative url as provided: %s. Please ensure that all urls are absolute.' % url)

        processed_urls.append(url)
        
        results = retrieve_url(url, user_agent)

        for res in results:

            lint_errors = []
            page_details = []
            additional_urls = []

            if res['code'] == 200 and is_internal_url(res['url']):

                lint_errors, page_details, links, sources = process_html(res['content'], res['url'])

                if links and len(links) > 0:
                    for url in links:
                        if is_relative_url(url):
                            url = make_url_absolute(url, res['url'])
                        if url not in processed_urls and url not in urls:
                            urls.append(url)

            res = store_results(db, run_id, res, lint_errors, page_details)

        time.sleep( delay / 1000.0 )


def retrieve_url(url, user_agent=None):

    def _build_payload(response):
        return {
            'url': response.url,
            'content': response.text,
            'code': response.status_code,
            'reason': response.reason,
            'size': len(response.text),
            'encoding': response.encoding,
        }
        return response.url

    headers = {}
    redirects = None
    if user_agent:
        headers['User-Agent'] = user_agent
        if 'Googlebot' in user_agent:
            # TODO: append ?__escaped_fragment__= to the url
            pass

    try:
        start = time.time()
        if is_internal_url(url):
            res = requests.get(url, headers=headers, timeout=15)
        else:
            res = requests.head(url, headers=headers, timeout=15)

        if len(res.history) > 0:


    except Exception, e:
        print e
        raise
        # TODO: Properly handle the failure. reraise?
    finally:
        request_time = time.time() - start


    
    return res.status_code, html, stats


def process_html(html, url):

    lint_errors = seolinter.lint(html)

    page_details = extract_page_details(html, url)

    internal_urls, external_urls = extract_links(html, url)

    sources = extract_sources(html)

    return lint_errors, page_details, internal_urls + external_urls, sources


def extract_links(html, url):
    internal = []
    external = []
    href_re = re.compile(r'<a.*?href=[\'"](?P<link>.*?)[\'"].*?>(?P<text>.*?)</a>')
    res = href_re.findall(html)
    if not res:
        return internal, external

    for r in res:
        link_data = {'url': r[0], 'text': r[1]}
        if is_internal_url(r[0]):
            internal.append(link_data)
        else:
            external.append(link_data)

    return internal, external


def extract_sources(html):
    pass


def extract_page_details(html, url):
    return {}


def store_results(db, run_id, stats, lint_errors, page_details, additional_urls):
    cur = db.cursor()

    pass


def is_internal_url(url):
    base_url = _get_base_url(url)
    link_re = re.compile(r'^(http(s)?:\/\/%s)?(\/.*)' % re.escape(base_url))
    return True if link_re.match(url) else False

def is_relative_url(url):
    return False


def make_url_absolute(url, source_url):
    return url

def _get_base_url(url):
    res = urlparse(url)
    return res.hostname

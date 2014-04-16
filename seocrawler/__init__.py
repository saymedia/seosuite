import time
import uuid
import requests
import re
import hashlib
from urlparse import urlparse, urljoin

import seolinter


def crawl(urls, db, internal=False, delay=0, user_agent=None):

    processed_urls = {}
    url_associations = {}
    run_id = uuid.uuid4()

    run_count = 0
    while len(urls) > 0:
        run_count += 1
        url = urls.pop(0)

        print "Processing (%d / %d): %s" % (run_count, len(urls), url)
        if not is_full_url(url):
            raise ValueError('A relative url as provided: %s. Please ensure that all urls are absolute.' % url)

        processed_urls[url] = None
        
        results = retrieve_url(url, user_agent)

        for res in results:

            lint_errors = []
            page_details = []

            if res['code'] == 200:

                lint_errors, page_details, links, sources = process_html(res['content'], res['url'])

                record = store_results(db, run_id, res, lint_errors, page_details)
                processed_urls[url] = record.id
                url_associations[url] = {}

                if links and len(links) > 0:
                    for link in links:
                        link_url = link['url']

                        # Process all external links and create the 
                        if not is_internal_url(link_url, url):
                            if link_url not in processed_urls:
                                link_results = retrieve_url(link_url, user_agent, False)

                                for link_result in link_results:
                                    if link_result['code'] not in (301, 302):
                                        link_store = store_results(db, run_id, link_result, [], [])
                                        processed_urls[link_result['url']] = link_store.id

                                # Associate links
                                associate_link(db, record.id, link_store.id, run_id, link.get('text'), link.get('alt'), link.get('rel'))

                        elif link_url not in processed_urls and link_url not in urls:
                            urls.append(link_url)
                            url_associations[url][link_url] = link
            else:
                record = store_results(db, run_id, res, lint_errors, page_details)
                processed_urls[url] = record.id

        time.sleep( delay / 1000.0 )

    # Process associations
    for url, associations in url_associations.iteritems():
        for association, link in associations.iteritems():
            if association in processed_urls:
                associate_link(db, processed_urls[url], processed_urls[association], run_id, link.get('text'), link.get('alt'), link.get('rel'))


def retrieve_url(url, user_agent=None, full=True):

    def _build_payload(response):
        return {
            'url': response.url,
            'url_length': len(response.url),
            'content': response.text,
            'content_type': response.headers.get('content-type'),
            'code': response.status_code,
            'reason': response.reason,
            'size': len(response.text),
            'encoding': response.encoding,
        }

    headers = {}
    redirects = []
    if user_agent:
        headers['User-Agent'] = user_agent
        if 'Googlebot' in user_agent:
            # TODO: append ?__escaped_fragment__= to the url
            pass

    try:
        if full:
            res = requests.get(url, headers=headers, timeout=15)
        else:
            res = requests.head(url, headers=headers, timeout=15)

        if len(res.history) > 0:
            redirects = [_build_payload(redirect) for redirect in res.history]

    except Exception, e:
        print e
        raise
        # TODO: Properly handle the failure. reraise?

    return [_build_payload(res),] + redirects


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
        link_url = make_full_url(r[0], url)
        link_data = {'url': link_url, 'text': r[1]}
        # print link_url
        if is_internal_url(link_url):
            internal.append(link_data)
        else:
            external.append(link_data)

    return internal, external


def extract_sources(html):
    return {}


def extract_page_details(html, url):
    return {}


def store_results(db, run_id, stats, lint_errors, page_details):
    cur = db.cursor()

    insert = '''
INSERT INTO crawl_urls VALUES (0,
    %s, 0, %s, %s,
    %s, %s, %s, %s, %s, %s, COMPRESS(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s)
    '''

    try:
        cur.execute(insert, (
            run_id,
            
            ))
        db.commit()
    except:
        db.rollback()


def is_internal_url(url):
    if is_full_url(url):
        base_url = _get_base_url(url)
        link_re = re.compile(r'^(http(s)?:\/\/%s)?(\/.*)' % re.escape(base_url))
        return True if link_re.match(url) else False
    else:
        return True

def is_full_url(url):
    link_re = re.compile(r'^(http(s)?:\/\/[a-zA-Z0-9\-_]+\.[a-zA-Z]+(.)+)+')
    return True if link_re.match(url) else False


def make_full_url(url, source_url):
    return urljoin(source_url, url)


def associate_link(db, from_id, to_id, text, alt, rel):
    pass

def _get_base_url(url):
    res = urlparse(url)
    return res.hostname

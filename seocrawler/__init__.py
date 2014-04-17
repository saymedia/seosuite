 # -*- coding: utf-8 -*-

import time
import uuid
import requests
import re
import hashlib
from urlparse import urlparse, urljoin

from bs4 import BeautifulSoup

import seolinter

html_parser = "lxml"
# html_parser = "html.parser"

TIMEOUT = 16

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

            lint_errors = {}
            page_details = {}

            if res['code'] == 200:

                lint_errors, page_details, links, sources = process_html(res['content'], res['url'])

                record = store_results(db, run_id, res, lint_errors, page_details)
                processed_urls[url] = record
                url_associations[url] = {}

                if links and len(links) > 0:
                    for link in links:
                        link_url = link['url']

                        if not link['valid']:
                            # Process any malformed links
                            bad_link = store_results(db, run_id, {
                                'url': link_url,
                                'code': 9999,
                                }, {}, {}, None, False)
                            processed_urls[link_url] = bad_link
                            associate_link(db, record, bad_link, run_id, link.get('text'), link.get('alt'), link.get('rel'))
                        elif not is_internal_url(link_url, url):
                            # Process all external links and create the
                            if link_url not in processed_urls:
                                link_results = retrieve_url(link_url, user_agent, False)

                                for link_result in link_results:
                                    if link_result['code'] not in (301, 302):
                                        link_store = store_results(db, run_id, link_result, {}, {}, True)
                                        processed_urls[link_result['url']] = link_store

                                # Associate links
                                associate_link(db, record, link_store, run_id, link.get('text'), link.get('alt'), link.get('rel'))

                        elif internal and link_url not in processed_urls and link_url not in urls:
                            urls.append(link_url)
                            url_associations[url][link_url] = link
            else:
                record = store_results(db, run_id, res, lint_errors, page_details, False)
                processed_urls[url] = record

        time.sleep( delay / 1000.0 )

    # Process associations
    for url, associations in url_associations.iteritems():
        for association, link in associations.iteritems():
            if association in processed_urls:
                associate_link(db, processed_urls[url], processed_urls[association], run_id, link.get('text'), link.get('alt'), link.get('rel'))


def retrieve_url(url, user_agent=None, full=True):

    def _build_payload(response, request_time):
        return {
            'url': response.url,
            'url_length': len(response.url),
            'content': response.text,
            'content_type': response.headers.get('content-type'),
            'code': int(response.status_code),
            'reason': response.reason,
            'size': len(response.text),
            'encoding': response.encoding,
            'response_time': request_time,
        }

    headers = {}
    redirects = []
    if user_agent:
        headers['User-Agent'] = user_agent
        if 'Googlebot' in user_agent:
            # TODO: append ?__escaped_fragment__= to the url
            pass

    try:
        start = time.time()
        if full:
            res = requests.get(url, headers=headers, timeout=TIMEOUT)
        else:
            res = requests.head(url, headers=headers, timeout=TIMEOUT)

        if len(res.history) > 0:
            redirects = [_build_payload(redirect) for redirect in res.history]

    except requests.exceptions.Timeout, e:
        return {
            'url': url,
            'url_length': len(url),
            'code': 0,
            'reason': 'Timeout %s' % TIMEOUT
            }
    except Exception, e:
        print e
        raise
    finally:
        request_time = time.time() - start        
        # TODO: Properly handle the failure. reraise?

    return [_build_payload(res, request_time),] + redirects


def process_html(html, url):

    lint_errors = seolinter.lint(html)

    page_details = extract_page_details(html, url)

    links = extract_links(html, url)

    sources = extract_sources(html)

    return lint_errors, page_details, links, sources


def extract_links(html, url):
    links = []
    soup = BeautifulSoup(html, html_parser)

    for a_tag in soup.find_all('a'):
        valid = True
        try:
            full_url = make_full_url(a_tag.get('href'), url)
        except Exception:
            full_url = a_tag.get('href')
            valid = False

        if full_url: # Ignore any a tags that don't have an href
            links.append({
                'url': full_url,
                'valid': valid,
                'text': a_tag.string or a_tag.get_text(),
                'alt': a_tag.get('alt'),
                'rel': a_tag.get('rel'),
                })

    return links


def extract_sources(html):
    sources = []

    soup = BeautifulSoup(html, html_parser)
    links = soup.find(['img', 'link', 'script', 'style'])

    for link in links:
        sources.append({
            'url': link.get('src') or link.get('href'),
            'alt_text': unicode(link.get('alt')),
            })

    return sources


def extract_page_details(html, url):
    soup = BeautifulSoup(html, html_parser)

    if not soup.find('head'):
        return {}

    robots = soup.find('head').find('meta', attrs={"name":"robots"})
    rel_next = soup.find('head').find('link', attrs={'rel':'next'})
    rel_prev = soup.find('head').find('link', attrs={'rel':'prev'})
    title = soup.title.get_text() if soup.title else unicode(soup.find('title'))
    meta_description = soup.find('head').find('meta', attrs={"name":"description"})
    canonical = soup.find('head').find('link', attrs={"rel":"canonical"})
    h1_1 = soup.find('h1')
    h1_2 = soup.find_all('h1')[1] if len(soup.find_all('h1')) > 1 else None

    return {
        'size': len(html),
        'canonical': canonical.get("href") if canonical else None,
        'title_1': title,
        'title_length_1': len(title),
        'meta_description_1': meta_description.get("content") if meta_description else None,
        'meta_description_length_1': len(meta_description) if meta_description else 0,
        'h1_1': h1_1.get_text() if h1_1 else None,
        'h1_length_1': len(h1_1.get_text()) if h1_1 else 0,
        'h1_2': h1_2.get_text() if h1_2 else None,
        'h1_length_2': len(h1_2.get_text()) if h1_2 else 0,
        'h1_count': len(soup.find_all('h1')),
        'meta_robots': robots.get("content") if robots else None,
        'rel_next': rel_next.get("href") if rel_next else None,
        'rel_prev': rel_prev.get('href') if rel_prev else None,
    }


def store_results(db, run_id, stats, lint_errors, page_details, external=False, valid=True):
    cur = db.cursor()

    insert = '''
INSERT INTO `crawl_urls` VALUES (
    0, %s, 0, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s)
    '''

    try:
        url = stats.get('url')
        content = stats.get('content', '')
        content_hash = hashlib.sha256(content.encode('ascii', 'ignore')).hexdigest()
        cur.execute(insert, (
            run_id,
            content_hash,                                       # content_hash

            # request data
            stats.get('url'),                                   # address
            _get_base_url(url) if valid else None,              # domain
            _get_path(url) if valid else None,                  # path
            1 if external else 0,                               # external
            stats.get('code'),                                  # status_code
            stats.get('reason'),                                # status
            stats.get('content', ''),                           # body
            stats.get('size'),                                  # size
            len(url),                                           # address_length
            stats.get('encoding'),                              # encoding
            stats.get('content_type'),                          # content_type
            stats.get('response_time'),                         # response_time
            None,                                               # redirect_uri
            page_details.get('canonical'),                      # canonical

            # parse data
            page_details.get('title_1'),                        # title_1
            page_details.get('title_length_1'),                 # title_length_1
            page_details.get('title_occurences_1'),             # title_occurences_1
            page_details.get('meta_description_1'),             # meta_description
            page_details.get('meta_description_length_1'),      # meta_description_length_1
            page_details.get('meta_description_occurrences_1'), # meta_description_occurrences_1
            page_details.get('h1_1'),                           # h1_1
            page_details.get('h1_length_1'),                    # h1_length_1
            page_details.get('h1_2'),                           # h1_2
            page_details.get('h1_length_2'),                    # h1_length_2
            page_details.get('h1_count'),                       # h1_count
            page_details.get('meta_robots'),                    # meta_robots
            page_details.get('rel_next'),                       # rel_next
            page_details.get('rel_prev'),                       # rel_prev

            # lint data
            len(lint_errors.get('critical', [])),               # lint_critical
            len(lint_errors.get('error', [])),                  # lint_error
            len(lint_errors.get('warn', [])),                   # lint_warn
            len(lint_errors.get('info', [])),                   # lint_info
            ''                                                  # lint_results
            ))
        db.commit()
    except:
        db.rollback()
        raise

    return cur.lastrowid


def is_internal_url(url, source_url):
    if is_full_url(url):
        base_url = _get_base_url(url)
        base_source_url = _get_base_url(source_url)
        return (
            base_url == base_source_url
            or (len(base_url) > len(base_source_url) and base_source_url == base_url[-len(base_source_url):])
            or (len(base_source_url) > len(base_url) and base_url == base_source_url[-len(base_url):])
            )
    else:
        return True

def is_full_url(url):
    link_re = re.compile(r'^(http(s)?:\/\/[a-zA-Z0-9\-_]+\.[a-zA-Z]+(.)+)+')
    return True if link_re.match(url) else False


def make_full_url(url, source_url):
    return urljoin(source_url, url)


def associate_link(db, from_id, to_id, run_id, text, alt, rel):
    cur = db.cursor()

    association = '''
INSERT INTO `crawl_links` VALUES(0, %s, null, %s, %s, %s, %s, %s)
    '''

    try:
        cur.execute(association, (
            run_id,
            from_id,
            to_id,
            text.encode('ascii', 'ignore') if text else None,
            alt.encode('ascii', 'ignore') if alt else None,
            rel,
            ))
        db.commit()
    except:
        db.rollback()
        raise

    return db.insert_id()

def _get_base_url(url):
    res = urlparse(url)
    return res.netloc

def _get_path(url):
    base = _get_base_url(url)
    parts = url.split(base)
    return parts[-1]

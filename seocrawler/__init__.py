import time
import uuid
import requests
import re
from urlparse import urlparse

import seolinter

sql_schema = """
CREATE TABLE `crawl_urls` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `level` tinyint(4) unsigned NOT NULL DEFAULT '0',
  `request_hash` varchar(36) DEFAULT NULL,
  `content_hash` varchar(64) DEFAULT NULL,
  `address` varchar(2048) NOT NULL DEFAULT '',
  `domain` varchar(128) DEFAULT NULL,
  `path` varchar(2048) NOT NULL DEFAULT '',
  `status_code` tinyint(3) unsigned DEFAULT NULL,
  `status` varchar(16) DEFAULT NULL,
  `body` text,
  `size` int(10) unsigned DEFAULT NULL,
  `address_length` int(10) unsigned NOT NULL,
  `encoding` varchar(16) NOT NULL DEFAULT '',
  `content_type` varchar(64) DEFAULT NULL,
  `response_time` float unsigned DEFAULT NULL,
  `redirect_uri` varchar(2048) DEFAULT NULL,
  `canonical` varchar(2048) DEFAULT NULL,
  `title_1` varchar(1024) DEFAULT NULL,
  `title_length_1` int(10) unsigned DEFAULT NULL,
  `title_occurences_1` int(10) unsigned DEFAULT NULL,
  `meta_description_1` varchar(2048) DEFAULT NULL,
  `meta_description_length_1` int(10) unsigned DEFAULT NULL,
  `meta_description_occurrences_1` int(10) unsigned DEFAULT NULL,
  `h1_1` varchar(2048) DEFAULT NULL,
  `h1_length_1` int(10) unsigned DEFAULT NULL,
  `h1_2` varchar(2048) DEFAULT NULL,
  `h1_length_2` int(10) unsigned DEFAULT NULL,
  `h1_count` int(10) unsigned DEFAULT NULL,
  `meta_robots` varchar(16) DEFAULT NULL,
  `rel_next` varchar(2048) DEFAULT NULL,
  `rel_prev` varchar(2048) DEFAULT NULL,
  `inlinks` int(10) unsigned DEFAULT NULL,
  `outlinks` int(10) unsigned DEFAULT NULL,
  `external_outlinks` int(10) unsigned DEFAULT NULL,
  `lint_critical` int(10) unsigned DEFAULT NULL,
  `lint_error` int(10) unsigned DEFAULT NULL,
  `lint_warn` int(10) unsigned DEFAULT NULL,
  `lint_info` int(10) unsigned DEFAULT NULL,
  `lint_results` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""

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
            pass

    except Exception, e:
        print e
        raise
        # TODO: Properly handle the failure. reraise?
    finally:
        request_time = time.time() - start



    return [_build_payload(res),]


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


def store_results(db, run_id, stats, lint_errors, page_details):
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

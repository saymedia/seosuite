import time
import uuid
import requests
import re
from urlparse import urlparse, urljoin

import seolinter

sql_schema = """
CREATE TABLE `crawl_links` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `request_hash` varchar(32) DEFAULT NULL,

  # request data
  `from_id` int(10) unsigned NOT NULL,
  `to_id` int(10) unsigned NOT NULL,
  `link_text` varchar(1024) DEFAULT NULL,
  `alt_text` varchar(1024) DEFAULT NULL,
  `rel` varchar(1024) DEFAULT NULL,

  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `from_id` (`from_id`),
  KEY `to_id` (`to_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `crawl_urls` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `run_id` varchar(36) NOT NULL DEFAULT '',
  `level` tinyint(4) unsigned NOT NULL DEFAULT '0',
  `request_hash` varchar(32) DEFAULT NULL,
  `content_hash` varchar(32) DEFAULT NULL,

  # request data
  `address` varchar(2048) NOT NULL DEFAULT '',
  `domain` varchar(128) DEFAULT NULL,
  `path` varchar(2048) NOT NULL DEFAULT '',
  `external` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `status_code` tinyint(4) unsigned DEFAULT NULL,
  `status` varchar(32) DEFAULT NULL,
  `body` blob,
  `size` int(10) unsigned DEFAULT NULL,
  `address_length` int(10) unsigned NOT NULL,
  `encoding` varchar(16) NOT NULL DEFAULT '',
  `content_type` varchar(64) DEFAULT NULL,
  `response_time` float unsigned DEFAULT NULL,
  `redirect_uri` varchar(2048) DEFAULT NULL,
  `canonical` varchar(2048) DEFAULT NULL,

  # parse data
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

  # link data
  # `inlinks` int(10) unsigned DEFAULT NULL,
  # `outlinks` int(10) unsigned DEFAULT NULL,
  # `external_outlinks` int(10) unsigned DEFAULT NULL,

  # lint data
  `lint_critical` int(10) unsigned DEFAULT NULL,
  `lint_error` int(10) unsigned DEFAULT NULL,
  `lint_warn` int(10) unsigned DEFAULT NULL,
  `lint_info` int(10) unsigned DEFAULT NULL,
  `lint_results` text,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""

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

<<<<<<< Updated upstream
        processed_urls.append(url)

=======
        processed_urls[url] = None
        
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    finally:
        request_time = time.time() - start



    return [_build_payload(res),]
=======
    
    return [_build_payload(res),] + redirects
>>>>>>> Stashed changes


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
    # cur = db.cursor()
    pass


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

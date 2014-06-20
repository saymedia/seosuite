# -*- coding: utf-8 -*-

import sys
import re
import robotparser

from bs4 import BeautifulSoup

CRITICAL = 0
ERROR = 1
WARN = 2
INFO = 3

levels = (
    'critical',
    'error',
    'warning',
    'info',
)

html_parser = "lxml"
# html_parser = "html.parser"

stop_words = ('a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'that',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'the',
            'to', 'was', 'were', 'will', 'with')

rules = [
    # for html
    ('C22', 'has head', CRITICAL),
    # ('E01', 'is utf8', ERROR),
    ('E02', 'has title', ERROR),
    ('E05', 'has meta description', ERROR),
    ('E08', 'has canonical', ERROR),
    ('E09', 'has h1', ERROR),
    ('E12', 'title matches <1 h1 word', ERROR),
    ('E13', 'title matches <1 meta description word', ERROR),
    ('E17', '<1000 outlinks on page', ERROR),
    ('W03', 'title < 58 chars', WARN),
    # ('W04', 'duplicate title', WARN),
    ('W06', 'meta description < 150 chars', WARN),
    # ('W07', 'duplicate meta description', WARN),
    ('W14', 'title matches <3 h1 words', WARN),
    ('W15', 'title matches <3 meta description word', WARN),
    ('W16', '<300 outlinks on page', WARN),
    ('W18', 'size < 200K', WARN),
    ('W19', 'all img tags have alt attribute', WARN),
    ('W23', 'h1 count > 1', WARN),
    ('I10', 'missing rel=prev', INFO),
    ('I11', 'missing rel=next', INFO),
    ('I20', 'has robots=nofollow', INFO),
    ('I21', 'has robots=noindex', INFO),

    # for robots.txt
    ('C23', 'has sitemap', CRITICAL),
    ('I24', 'has disallow', INFO),
    ('I25', 'has user-agent', INFO),

    # for sitemap index
    ('C26', 'is valid xml', CRITICAL),
    ('C27', 'has locs', CRITICAL),
    ('E33', '<1000 locs in index', ERROR),

    # for sitemap urlset
    ('I30', 'has priority', INFO),
    ('I31', 'has changefreq', INFO),
    ('I32', 'has lastmod', INFO),
]

def get_rules():
    return rules

def parse_html(html):
    soup = BeautifulSoup(html, html_parser)

    if not soup.find('head'):
        return {
            'head': False
        }

    robots = soup.find('head').find('meta', attrs={"name":"robots"})
    title = soup.title.get_text() if soup.title else unicode(soup.find('title'))
    h1s = soup.find_all('h1')
    h1 = soup.find('h1') or h1s[0] if len(h1s) >= 1 else None
    meta_description = soup.find('head').find('meta', attrs={"name":"description"})

    return {
        'head': soup.find('head'),
        'title': title,
        'title_keywords': extract_keywords(title),
        'canonical': soup.find('head').find('link', attrs={"rel":"canonical"}),
        'next': soup.find('head').find('link', attrs={"rel":"next"}),
        'prev': soup.find('head').find('link', attrs={"rel":"prev"}),
        'robots': robots.get("content") if robots else None,
        'meta_description': meta_description,
        'meta_description_keywords':
            extract_keywords(meta_description.get('content')) if meta_description else [],
        'h1': h1,
        'h1s': h1s,
        'h1_count': len(h1s),
        'h1_keywords': extract_keywords(h1.get_text()) if h1 else [],
        # 'text_only': soup.get_text(),
        'links': soup.find_all('a'),
        'link_count': len(soup.find_all('a')),
        'meta_tags': soup.find('head').find_all('meta'),
        'images': soup.find_all('img'),
        'size': len(html),
    }

def parse_sitemap(xml):
    soup = BeautifulSoup(xml, html_parser)

    if soup.find('sitemapindex'):
        return ('index', _parse_sitemapindex(soup))
    elif soup.find('urlset'):
        return ('urlset', _parse_sitemapurlset(soup))
    else:
        raise Exception('invalid sitemap')

def _parse_sitemapurlset(soup):
    # find all the <url> tags in the document
    urls = soup.findAll('url')

    # no urls? bail
    if not urls:
        return False

    # storage for later...
    out = []

    #extract what we need from the url
    for u in urls:
        out.append({
            'loc': u.find('loc').string if u.find('loc') else None,
            'priority': u.find('priority').string if u.find('priority') else None,
            'changefreq': u.find('changefreq').string if u.find('changefreq') else None,
            'lastmod': u.find('lastmod').string if u.find('lastmod') else None,
            })
    return out

def _parse_sitemapindex(soup):
    # find all the <url> tags in the document
    sitemaps = soup.findAll('sitemap')

    # no sitemaps? bail
    if not sitemaps:
        return False

    # storage for later...
    out = []

    #extract what we need from the url
    for u in sitemaps:
        out.append({
            'loc': u.find('loc').string if u.find('loc') else None
            })
    return out

# Example sitemap
'''
# Tempest - biography

User-agent: *
Disallow: /search

Sitemap: http://www.biography.com/sitemaps.xml
'''
def parse_robots_txt(txt):
    # TODO: handle disallows per user agent
    sitemap = re.compile("Sitemap:\s+(.+)").findall(txt)
    disallow = re.compile("Disallow:\s+(.+)").findall(txt)
    user_agent = re.compile("User-agent:\s+(.+)").findall(txt)
    return {
        'sitemap': sitemap,
        'disallow': disallow,
        'user_agent': user_agent
    }

def extract_keywords(text):
    # We probably don't care about words shorter than 3 letters
    min_word_size = 3
    text = unicode(text)
    if text:
        return [kw.lower()
            for kw in re.sub('[^A-Za-z0-9\-\']', ' ', text).split()
            if kw not in stop_words and len(kw) >= min_word_size]
    else:
        return []

def word_match_count(a, b):
    count = 0
    for word1 in a:
        for word2 in b:
            if word1 == word2:
                count = count + 1
    return count

def lint_html(html_string, level=INFO):
    output = {}

    p = parse_html(html_string)

    # stop and return on critical errors
    if not p['head']:
        output['C22'] = True
        return output

    if not p['title']:
        output['E02'] = True
    elif len(p['title']) > 58:
        output['W03'] = True

    if not p['meta_description']:
        output['E05'] = True
    elif len(p['meta_description'].get('content')) > 150:
        output['W06'] = True

    if not p['canonical']:
        output['E08'] = True

    if not p['h1']:
        output['E09'] = True

    if not p['next']:
        output['I10'] = True

    if not p['prev']:
        output['I11'] = True

    if p['link_count'] >= 300:
        output['W16'] = p['link_count']

    if p['link_count'] >= 1000:
        output['E17'] = p['link_count']

    if p['size'] >= 200 * 1024:
        output['E18'] = p['size']

    if p['robots'] and "nofollow" in p['robots']:
        output['I20'] = p['robots']

    if p['robots'] and "noindex" in p['robots']:
        output['I21'] = p['robots']

    if p['h1_count'] >= 1:
        output['W23'] = p['h1_count']

    if word_match_count(p['title_keywords'], p['h1_keywords']) < 1:
        output['E12'] = (word_match_count(p['title_keywords'], p['h1_keywords']), p['title_keywords'], p['h1_keywords'])

    if word_match_count(p['title_keywords'], p['meta_description_keywords']) < 1:
        output['E13'] = (word_match_count(p['title_keywords'], p['meta_description_keywords']), p['title_keywords'], p['meta_description_keywords'])

    if word_match_count(p['title_keywords'], p['h1_keywords']) < 3:
        output['W14'] = (word_match_count(p['title_keywords'], p['h1_keywords']), p['title_keywords'], p['h1_keywords'])

    if word_match_count(p['title_keywords'], p['meta_description_keywords']) < 3:
        output['W15'] = (word_match_count(p['title_keywords'], p['meta_description_keywords']), p['title_keywords'], p['meta_description_keywords'])

    images_missing_alt = []
    for image in p['images']:
        if not image.get("alt"):
            images_missing_alt.append(image)

    if len(images_missing_alt) > 0:
        output['W19'] = len(images_missing_alt)

    # remove rules below level requested
    if level < INFO:
        for rule in rules:
            for key, value in output.iteritems():
                if rule[2] < level:
                    output[key].remove()

    return output

def lint_sitemap(xml_string, level=INFO):
    output = {}

    try:
        p = parse_sitemap(xml_string)
    except Exception, e:
        output['C26'] = True
        return output

    if p[0] == 'index':
        output = _lint_sitemapindex(p[1])
    elif p[0] == 'urlset':
        output = _lint_sitemapurlset(p[1])
    else:
        output['C26'] = True
        return output

    # remove rules below level requested
    if level < INFO:
        for rule in rules:
            for key, value in output.iteritems():
                if rule[2] < level:
                    output[key].remove()

    return output

def _lint_sitemapindex(p):
    output = {}

    if not p or len(p) == 0:
        output['C27'] = True
        return output

    if not len(p) < 10000:
        output['E33'] = True

    return output

def _lint_sitemapurlset(p):
    output = {}

    if not p or len(p) == 0:
        output['C27'] = True
        return output

    if not len(p) < 10000:
        output['E33'] = True

    for url in p:
        if url['priority']:
            output['I30'] = True
        if url['changefreq']:
            output['I31'] = True
        if url['lastmod']:
            output['I32'] = True

    return output

def lint_robots_txt(txt_string, level=INFO):
    output = {}

    p = parse_robots_txt(txt_string)

    # stop and return on critical errors
    if not p['sitemap']:
        output['C23'] = True
        return output

    if not p['disallow']:
        output['I24'] = True

    if not p['user_agent']:
        output['I25'] = True

    # remove rules below level requested
    if level < INFO:
        for rule in rules:
            for key, value in output.iteritems():
                if rule[2] < level:
                    output[key].remove()

    return output

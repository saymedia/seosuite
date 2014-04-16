 #!/usr/bin/python
 # -*- coding: utf-8 -*-

# usage:
# > curl http://fashionista.com/?__escaped_fragment__= | python seolinter/__init__.py
# or
# seolinter.lint(requests.get('http://fashionista.com/?__escaped_fragment__=').text)

import sys
import re

from bs4 import BeautifulSoup

CRITICAL = 0
ERROR = 1
WARN = 2
INFO = 3
DEBUG = 4

levels = (
    'critical',
    'error',
    'warning',
    'info',
    'debug',
)

html_parser = "lxml"
# html_parser = "html.parser"

stop_words = ('a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'that',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'the',
            'to', 'was', 'were', 'will', 'with')

rules = [
    ('E01', 'utf8', ERROR),
    ('E02', 'has title', ERROR),
    ('W03', 'title < 58 chars', WARN),
    # ('W04', 'duplicate title', WARN),
    ('E05', 'has meta description', ERROR),
    ('W06', 'meta description < 150 chars', WARN),
    # ('W07', 'duplicate meta description', WARN),
    ('E08', 'has canonical', ERROR),
    ('E09', 'has h1', ERROR),
    ('I10', 'missing rel=prev', INFO),
    ('I11', 'missing rel=next', INFO),
    ('E12', 'title matches <1 h1 word', ERROR),
    ('E13', 'title matches <1 meta description word', ERROR),
    ('W14', 'title matches <3 h1 words', WARN),
    ('W15', 'title matches <3 meta description word', WARN),
    ('W16', '<300 outlinks on page', WARN),
    ('E17', '<1000 outlinks on page', ERROR),
    ('W18', 'size < 200K', WARN),
    ('W19', 'all img tags have alt attribute', WARN),
    ('I20', 'has robots=nofollow', INFO),
    ('I21', 'has robots=noindex', INFO),
    ('C22', 'has head', CRITICAL),
    ('W23', 'h1 count > 1', WARN),
]

def parse_html(html):
    soup = BeautifulSoup(html, html_parser)

    if not soup.find('head'):
        return {
            'head': False
        }

    robots = soup.find('head').find('meta', attrs={"name":"robots"})
    title = soup.title.get_text() if soup.title else unicode(soup.find('title'))
    h1 = soup.find('h1') or soup.find_all('h1')[1]

    print soup.find('head').find('meta', attrs={"name":"description"})

    return {
        'head': soup.find('head'),
        'title': title,
        'title_keywords': extract_keywords(title),
        'canonical': soup.find('head').find('link', attrs={"rel":"canonical"}),
        'next': soup.find('head').find('link', attrs={"rel":"next"}),
        'prev': soup.find('head').find('link', attrs={"rel":"prev"}),
        'robots': robots.get("content") if robots else None,
        'meta_description': soup.find('head').find('meta', attrs={"name":"description"}),
        'meta_description_keywords':
            extract_keywords(soup.find('head').find('meta', attrs={"name":"description"}).get('content')),
        'h1': h1,
        'h1s': soup.find_all('h1'),
        'h1_count': len(soup.find_all('h1')),
        'h1_keywords': extract_keywords(h1.get_text()),
        'text_only': soup.get_text(),
        'links': soup.find_all('a'),
        'link_count': len(soup.find_all('a')),
        'meta_tags': soup.find('head').find_all('meta'),
        'images': soup.find_all('img'),
        'size': len(html),
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

def lint(html_string, level=INFO):
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
        output['E17'] = p['size']

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
        output['E14'] = (word_match_count(p['title_keywords'], p['h1_keywords']), p['title_keywords'], p['h1_keywords'])

    if word_match_count(p['title_keywords'], p['meta_description_keywords']) < 3:
        output['E15'] = (word_match_count(p['title_keywords'], p['meta_description_keywords']), p['title_keywords'], p['meta_description_keywords'])

    images_missing_alt = []
    for image in p['images']:
        if not image.get("alt"):
            images_missing_alt.append(image)

    if len(images_missing_alt) > 0:
        output['W19'] = images_missing_alt

    # for rule in rules:
    #     for key in output:
            # what was I doing here?

    return output


def main():
    html_string = sys.stdin.read()
    output = lint(html_string)

    exit = 0

    for rule in rules:
        for key, value in output.iteritems():
            if key == rule[0]:
                print rule[0] + ':', rule[1], '(' + levels[rule[2]] + ')'
                if value != True:
                    print "\tfound:", value
                if rule[2] == ERROR or rule[2] == CRITICAL:
                    exit = 1

    # if exit:
    #     print html_string

    sys.exit(exit)

if __name__ == '__main__':
    main()

import gevent
from gevent import monkey
monkey.patch_all()

import re
from urllib import urlopen
from argparse import ArgumentParser
from collections import defaultdict
from operator import itemgetter
from lxml.cssselect import CSSSelector
from lxml.html import parse
from lxml import etree


def extract_keywords(text):
    # We probably don't care about words shorter than 3 letters
    min_word_size = 3
    if text:
        return [kw.lower()
                for kw in re.sub('[^A-Za-z0-9\-\']', ' ', text).split()
                if kw not in get_stop_words() and len(kw) >= min_word_size]
    else:
        return []


def keywords_for_tag(tree, tag, attr=None):
    sel = CSSSelector(tag)
    keywords = []
    for e in sel(tree):
        if attr:
            text = e.get(attr, '')
        else:
            text = e.text
        keywords.extend(extract_keywords(text))
    return keywords


def print_keywords(title, kw):
    kw = " ".join(kw)
    if kw:
        print
        print "*** %s keywords ***" % title
        print kw


def tags(tree):
    check_tags = ['title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'strong', 'em', 'p', 'li']
    for tag in check_tags:
        print_keywords(tag, keywords_for_tag(tree, tag))

    check_attrs = [('img', 'alt'), ('img', 'title')]
    for tag, attr in check_attrs:
        print_keywords("%s:%s" % (tag, attr),
                       keywords_for_tag(tree, tag, attr))


def count_keywords(tree):
    keywords = defaultdict(int)
    for e in tree.iter():
        if e.tag not in ('script', 'style'):
            for kw in extract_keywords(e.text):
                keywords[kw] += 1.0
    return (keywords.items(), sum(count for count in keywords.values()))


def frequency(tree, ngram_size=1):
    if ngram_size == 1:
        keywords, total = count_keywords(tree)
    else:
        keywords, total = count_ngrams(tree, ngram_size)
    keywords.sort(key=itemgetter(1), reverse=True)
    for kw, count in keywords:
        if count > 1:
            print "%4d %s (%.2f%%)" % (count, kw, ((count / total) * 100))


def count_ngrams(tree, size):
    text = []
    ngrams = defaultdict(int)
    for e in tree.iter():
        if e.tag not in ('script', 'style'):
            text.extend(extract_keywords(e.text))

    for ii in xrange(len(text)):
        ngram = text[ii:ii+size]
        ngrams[' '.join(ngram)] += 1.0

    return (ngrams.items(), sum(count for count in ngrams.values()))


def get_stop_words():
    return ('a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that',
            'the', 'to', 'was', 'were', 'will', 'with')


def get_http_status(url):
    if url.startswith('http'):
        return urlopen(url).getcode()
    else:
        return 'UNKNOWN'


def check_links(url, tree, timeout=20):
    root = tree.getroot()
    root.make_links_absolute(url)
    urls = set()
    for el, attr, link, pos in root.iterlinks():
        urls.add(link)
    print "Checking %d links..." % len(urls)

    job_urls = {}
    jobs = []
    for url in urls:
        job = gevent.spawn(get_http_status, url)
        jobs.append(job)
        job_urls[job] = url

    gevent.joinall(jobs, timeout=timeout)
    for job in jobs:
        url = job_urls[job]
        if job.value:
            status = job.value
        else:
            status = 'TIMEOUT'
        if status != 200:
            print "%s - %s" % (status, url)


def main():
    p = ArgumentParser(description='Checks on-page factors. Very basic.')
    p.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                   help='print detailed output')
    p.add_argument('-t', '--timeout', dest='timeout', type=int,
                   default=20,
                   help='timeout in seconds (default 20)')
    p.add_argument('action', type=str,
                   choices=('tags', 'frequency', 'digrams', 'trigrams',
                            'check-links')),
    p.add_argument('url', type=str,
                   help='url to check')
    args = p.parse_args()
    print "Fetching %s" % args.url
    webf = urlopen(args.url)
    tree = parse(webf)

    if args.action == 'tags':
        tags(tree)
    elif args.action == 'frequency':
        frequency(tree)
    elif args.action == 'digrams':
        frequency(tree, ngram_size=2)
    elif args.action == 'trigrams':
        frequency(tree, ngram_size=3)
    elif args.action == 'check-links':
        check_links(args.url, tree, timeout=args.timeout)


if __name__ == '__main__':
    main()
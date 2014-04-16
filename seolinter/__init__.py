 #!/usr/bin/python
 # -*- coding: utf-8 -*-

# usage:
# > curl http://fashionista.com/?__escaped_fragment__= | python seolinter/__init__.py
# or
# seolinter.lint(requests.get('http://fashionista.com/?__escaped_fragment__=').text)

import sys
from bs4 import BeautifulSoup

CRITICAL = 'crit'
ERROR = 'err'
WARN = 'warn'
INFO = 'info'
DEBUG = 'debug'

rules = [
    ('E01', 'utf8', ERROR),
    ('E02', 'has title', ERROR),
    ('W03', 'title < 58 chars', WARN),
    ('W04', 'duplicate title', WARN),
    ('E05', 'has meta description', ERROR),
    ('W06', 'meta description < 150 chars', WARN),
    ('W07', 'duplicate meta description', WARN),
    ('E08', 'has canonical', ERROR),
    ('E09', 'has h1', ERROR),
    ('I10', 'rel=prev', INFO),
    ('I11', 'rel=next', INFO),
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
]

def lint(html_string):
    output = {}

    soup = BeautifulSoup(html_string)

    if not soup.find('head'):
        # hack for xml sitemaps
        return {
            'C22': CRITICAL
        }

    for rule in rules:
        if rule[0] == 'E01':
            output['E01'] = ERROR
        if rule[0] == 'E02':
            output['E02'] = ERROR
        if rule[0] == 'W03':
            output['W03'] = WARN

    return output


def main():
    webf = sys.stdin.read()
    out = lint(webf)
    print out

if __name__ == '__main__':
    main()

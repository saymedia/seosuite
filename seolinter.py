#!/usr/bin/env python
# -*- coding: utf-8 -*-

# usage:
# > python seolinter.py [text] [format]
# example:
# > cat robots.txt | seolinter.py --format=txt
# > curl http://www.biography.com/sitemaps.xml | seolinter.py

import optparse
import sys
import re

import seolinter

def run(options, args):
    stdin = sys.stdin.read()

    if options.format == 'auto':
        if not re.compile("\<").match(stdin):
            options.format = 'txt'
        elif not re.compile("\<html").match(stdin):
            options.format = 'xml'
        else:
            options.format = 'html'

    if options.format == 'html':
        output = seolinter.lint_html(stdin)
    if options.format == 'xml':
        output = seolinter.lint_sitemap(stdin)
    if options.format == 'txt':
        output = seolinter.lint_robots_txt(stdin)

    exit = 0

    for rule in seolinter.rules:
        for key, value in output.iteritems():
            if key == rule[0]:
                print rule[0] + ':', rule[1], '(' + seolinter.levels[rule[2]] + ')'
                if value != True:
                    print "\tfound:", value
                if rule[2] == seolinter.ERROR or rule[2] == seolinter.CRITICAL:
                    exit = 1

    # if exit:
    #     print html_string

    sys.exit(exit)

if __name__ == "__main__":
    parser = optparse.OptionParser(description='Validates html, sitemap xml and robots.txt content for common errors.')

    parser.add_option('-f', '--format', type="string", default='auto',
        help='The type of file to parse.')

    (options, args) = parser.parse_args()

    run(options, args)

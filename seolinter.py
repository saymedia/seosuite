#!/usr/bin/env python
# -*- coding: utf-8 -*-

# usage:
# > python seolinter.py [text] [format] [run_id]
# example:
# > cat robots.txt | seolinter.py --format=txt

import optparse
import sys

import seolinter

def run(options, args):
    stdin = "".join(sys.stdin.readlines())

    if options.format == 'html':
        print seolinter.lint_html(stdin)
    if options.format == 'xml':
        print seolinter.parse_sitemap(stdin)
    if options.format == 'txt':
        print seolinter.parse_robots_txt(stdin)
    if options.format == 'auto':
        print seolinter.parse_html(stdin)

if __name__ == "__main__":
    parser = optparse.OptionParser(description='Validates html, sitemap xml and robots.txt content for common errors.')

    parser.add_option('-f', '--format', type="string", default='auto',
        help='The type of file to parse.')

    (options, args) = parser.parse_args()

    run(options, args)

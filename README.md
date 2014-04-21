SEO Tool Suite
==============

Recluse is a suite of SEO tools for discovering and investigating common SEO issues across a domain.

- **SEO Crawler** crawls a site and saves the results to the db.
- **SEO Linter** checks HTML against common SEO rules.
- **SEO Reporter** outputs the crawl reports in various formats.
- **SEO Dashboard** displays the crawl data for the browser.


SEO Crawler
===========

SEO Crawler takes a given url and continues to crawl the internal links on the site until it can't find new urls to crawl. The crawler saves common request information like status code and content type. It also runs the SEO Linter to check for common SEO issues. The results of a crawl are saved to a database for later investigation and a JUnit report is saved to the file system. The idea is to catch basic, common errors across a whole site and allow for investigation into edge cases.

Instructions
------------

    > pip install -r requirements.txt
    > cat schema.sql | mysql -uusername -p
    > cp testurls.example testurls
    > cp config.yaml.example config.yaml
    > ./seocrawler.py http://fashionista.com

CLI Options
-----------

    $> python seocrawler.py --help
    Usage: seocrawler.py [options]
    
    Crawl the given url(s) and check them for SEO or navigation problems.
    
    Options:
      -h, --help            show this help message and exit
      -i, --internal        Crawl any internal link urls that are found in the
                            content of the page.
      --user-agent=USER_AGENT
                            The user-agent string to request pages with.
      --delay=DELAY         The number of milliseconds to delay between each
                            request.
      --database=DATABASE   A yaml configuration file with the database
                            configuration properties.
      -o OUTPUT, --output=OUTPUT
                            The path of the file where the output junix xml will
                            be written to.
    
      Input Options:
        -f FILE, --file=FILE
                            A file containing a list of urls (one url per line) to
                            process.
        -u BASE_URL, --base_url=BASE_URL
                            A single url to use as a starting point for crawling.
        -r RUN_ID, --run_id=RUN_ID
                            The id from a previous run to resume.
        -y YAML, --yaml=YAML
                            A yaml file containing a list of urls to process. The
                            yaml file should have a section labeled
                            "seocrawlerurls" that contains a list of the urls to
                            crawl.

SEO Linter
==========

The SEO Linter tests a given string for common SEO rules. The levels (CRITICAL, ERROR, WARN and INFO) are not hard, fast SEO rules but should help in an SEO investigation.

Instructions
------------

    > pip install -r requirements.txt
    > curl --silent http://fashionista.com?__escaped_fragment__= | python seolinter/__init__.py

Lint Rules
----------

- E02: has title (ERROR)
- W03: title < 58 chars (WARN)
- E05: has meta description (ERROR)
- W06: meta description < 150 chars (WARN)
- E08: has canonical (ERROR)
- E09: has h1 (ERROR)
- I10: missing rel=prev (INFO)
- I11: missing rel=next (INFO)
- E12: title matches <1 h1 word (ERROR)
- E13: title matches <1 meta description word (ERROR)
- W14: title matches <3 h1 words (WARN)
- W15: title matches <3 meta description word (WARN)
- W16: <300 outlinks on page (WARN)
- E17: <1000 outlinks on page (ERROR)
- W18: size < 200K (WARN)
- W19: all img tags have alt attribute (WARN)
- I20: has robots=nofollow (INFO)
- I21: has robots=noindex (INFO)
- C22: has head (CRITICAL)
- W23: h1 count > 1 (WARN)


SEO Reporter
============

The SEO Reporter takes a run_id, gets report data, then outputs it in a given format. The main use-case is running reports in Jenkins with JUnit. By default, it outputs the latest run as junit.

Instructions
------------

    > pip install -r requirements.txt
    # python seoreporter/__init__.py [type] [format] [run_id]
    > python seoreporter/__init__.py build junit d09b8571-5c8a-42ff-8ab7-c38f4f8871c4


SEO Dashboard
=============

The SEO Dashboard presents a table of crawl data as a table viewable in the browser.

Instructions
------------

    > pip install -r requirements.txt
    > python seodashboard/main.py
    > open localhost:5000


MIT License
===========

Copyright (c) 2014 Say Media Ltd

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

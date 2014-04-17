SEO Crawler
===========

SEO Crawler takes a given url and continues to crawl the internal links on the site until it can't find new urls to crawl. The crawler saves common request information like status code and content type. It also runs the SEO Linter to check for common SEO issues. The results of a crawl are saved to a database for later investigation. The idea is to catch basic, common errors across a whole site and allow for investigation into edge cases.

Instructions
------------

    > pip install -r requirements.txt
    > cat schema.sql | mysql -uusername -p
    > cp testurls.example testurls
    > cp config.yaml.example config.yaml
    > ./seocrawler.py http://fashionista.com


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
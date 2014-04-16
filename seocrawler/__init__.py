

def crawl(urls, db, internal=False):

    for url in urls:
        html, stats = retrieve_url(url)


def retrieve_url(url):
    html = None
    stats = {}
    
    return html, stats
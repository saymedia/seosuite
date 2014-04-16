import time
import uuid

def crawl(urls, db, internal=False, delay=0):

    processed_urls = []
    run_id = uuid.uuid4()

    while len(urls) > 0:
        url = urls.pop(0)
        processed_urls.append(url)
        
        status_code, html, stats = retrieve_url(url)
        
        if status_code == 200:

            lint_errors, page_details, additional_urls = process_html(html, url)

            if internal and len(additional_urls) > 0:
                for url in additional_urls:
                    if url not in processed_urls and url not in urls:
                        urls.append(url)

        else:
            # Process the error
            lint_errors = []
            page_details = []
            additional_urls = []

        store_results(db, run_id, stats, lint_errors, page_details,
            additional_urls)

        time.sleep( delay / 1000.0 )


def retrieve_url(url):
    html = None
    stats = {
        'result_code': 200,
        'result_message': None,
        'page_size': 1000,
        'duration': 200,
    }
    status_code = 200
    
    return status_code, html, stats


def process_html(html, url):
    lint_errors = []

    # Call seolint.lint(html)

    page_details = extract_page_details(html, url)

    additional_urls = extract_internal_urls(html, url)

    return lint_errors, page_details, additional_urls


def extract_internal_urls(html, url):
    return []


def extract_page_details(html, url):
    return {}


def store_results(db, run_id, stats, lint_errors, page_details, additional_urls):
    cur = db.cursor()

    pass
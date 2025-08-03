import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Set
import re

def extract_links(
    start_url: str,
    timeout: int = 10,
    delay: float = 0.5,
    max_pages: int = 50
) -> List[str]:
    """
    Crawl a careers listing starting at `start_url`, following static pagination links
    to collect all job URLs. Heuristics for pagination anchors include:
      - link text that’s a number (page indexes)
      - link text ‘next’, ‘>’, ‘>>’, ‘›’, ‘»’
      - href containing ‘page’ followed by digits

    Sleeps `delay` seconds between requests, and stops after `max_pages` pages.
    """
    visited_pages: Set[str] = set()
    pages_to_visit: List[str] = [start_url]
    job_urls: Set[str] = set()
    page_count = 0

    PAGINATION_TEXT = re.compile(r'^(?:next|>\>|\>|\»|\›)$', re.IGNORECASE)
    PAGINATION_HREF = re.compile(r'page[=/\-]?\d+', re.IGNORECASE)

    while pages_to_visit and page_count < max_pages:
        url = pages_to_visit.pop(0)
        if url in visited_pages:
            continue
        visited_pages.add(url)
        page_count += 1

        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️ Warning: could not fetch {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')

        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'job' in href.lower():
                full = href if href.startswith(('http://', 'https://')) else urljoin(url, href)
                job_urls.add(full)

        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)

            is_number = text.isdigit()
            is_nav = bool(PAGINATION_TEXT.match(text))
            is_href_page = bool(PAGINATION_HREF.search(href))

            if is_number or is_nav or is_href_page:
                full = href if href.startswith(('http://', 'https://')) else urljoin(url, href)
                if full not in visited_pages and full not in pages_to_visit:
                    pages_to_visit.append(full)

        time.sleep(delay)

    return sorted(job_urls)

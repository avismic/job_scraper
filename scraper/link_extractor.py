import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_links(url: str, timeout: int = 10) -> list[str]:
    """
    Crawls a career homepage and returns all job-like links.
    Naively filters anchors containing 'job' in their href.
    """
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    urls = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'job' in href.lower():
            # normalize relative URLs
            full = href if href.startswith('http') else urljoin(url, href)
            urls.add(full)
    return list(urls)

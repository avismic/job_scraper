import requests
from bs4 import BeautifulSoup

def scrape(url, timeout=10):
    """
    Fetches a URL and returns the main text content.
    """
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Remove nav and footer early
    for tag in soup.find_all(['nav', 'footer']):
        tag.decompose()

    # Prefer <main> or <article>, else full body
    container = soup.find(['main', 'article'])
    text = container.get_text(separator='\n', strip=True) if container else soup.get_text(separator='\n', strip=True)
    return text

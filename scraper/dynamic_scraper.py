from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape(url: str, timeout: int = 30) -> str:
    """
    Uses Playwright to render JS-heavy pages, then extracts main text like static_scraper.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout * 1000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')

    # Remove nav/footer
    for tag in soup.find_all(['nav', 'footer']):
        tag.decompose()

    # Prefer <main> or <article>
    container = soup.find(['main', 'article'])
    if container:
        return container.get_text(separator='\n', strip=True)
    return soup.get_text(separator='\n', strip=True)

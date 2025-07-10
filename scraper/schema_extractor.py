import requests
import extruct
from w3lib.html import get_base_url
from bs4 import BeautifulSoup


def extract_jobposting_schema(url: str, html: str) -> dict | None:
    """
    Extracts a schema.org JobPosting JSON-LD block from the page HTML.
    Returns a dict of canonical fields or None if no JobPosting is found.

    Fields returned (keys may be missing or empty):
      - title
      - company
      - city
      - country
      - employmentType
      - salaryLow
      - salaryHigh
      - currency
    """
    base_url = get_base_url(html, url)
    data = extruct.extract(html, base_url=base_url, syntaxes=["json-ld"]) or {}
    json_ld = data.get("json-ld", [])

    for item in json_ld:
        if isinstance(item, dict) and item.get("@type") == "JobPosting":
            job = item
            # Initialize record
            rec: dict = {}
            rec['title'] = job.get('title', '') or ''
            rec['company'] = job.get('hiringOrganization', {}).get('name', '') or ''

            # Location (take first if multiple)
            locations = job.get('jobLocation', [])
            if locations and isinstance(locations, list):
                addr = locations[0].get('address', {})
                rec['city'] = addr.get('addressLocality', '') or ''
                rec['country'] = addr.get('addressCountry', '') or ''
            else:
                rec['city'] = ''
                rec['country'] = ''

            # Employment type
            rec['employmentType'] = job.get('employmentType', '') or ''

            # Salary
            base_salary = job.get('baseSalary', {})
            if isinstance(base_salary, dict):
                value = base_salary.get('value', {})
                rec['salaryLow'] = str(value.get('minValue', ''))
                rec['salaryHigh'] = str(value.get('maxValue', ''))
                rec['currency'] = value.get('currency', '') or ''
            else:
                rec['salaryLow'] = ''
                rec['salaryHigh'] = ''
                rec['currency'] = ''

            return rec
    return None

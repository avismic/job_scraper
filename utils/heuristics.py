import re
from typing import Tuple

# Salary extraction regex covers ranges like ₹50,000 - ₹70,000, $100k-$120k, etc.
salary_pattern = re.compile(
    r"(?P<currency>[₹$€])\s*"
    r"(?P<low>[\d,]+)(?:[kK]?)(?:\s*[-–to]+\s*)"
    r"(?P<high>[\d,]+)(?:[kK]?)"
)

# Office type keywords
remote_kw = re.compile(r"\b(remote|work from home|telecommute)\b", flags=re.I)
hybrid_kw = re.compile(r"\b(hybrid)\b", flags=re.I)

# Experience level mapping
experience_levels = {
    r"\bintern\b": "Intern",
    r"\bentry[- ]level\b": "Entry-Level",
    r"\bassociate\b": "Associate/Mid-Level",
    r"\bmid[- ]level\b": "Associate/Mid-Level",
    r"\bsenior\b": "Senior-Level",
    r"\bmanager\b": "Managerial",
    r"\bexecutive\b": "Executive"
}

industries_map = {
    'tech': "Tech",
    'health': "Healthcare",
    'market': "Marketing",
    'consult': "Consulting",
    'finance': "Finance",
    'manufactur': "Manufacturing"
}


def extract_salary(text: str) -> Tuple[str, str, str]:
    """
    Returns (currency, salaryLow, salaryHigh) or ('','','') if not found.
    """
    match = salary_pattern.search(text)
    if match:
        cur = match.group('currency')
        low = match.group('low').replace(',', '')
        high = match.group('high').replace(',', '')
        return cur, low, high
    return '', '', ''


def extract_office_type(text: str) -> str:
    """
    Returns one of: Remote, Hybrid, In-Office.
    """
    if remote_kw.search(text):
        return 'Remote'
    if hybrid_kw.search(text):
        return 'Hybrid'
    return 'In-Office'


def extract_experience_level(text: str) -> str:
    """
    Maps common keywords to standardized experience levels.
    """
    txt = text.lower()
    for pattern, level in experience_levels.items():
        if re.search(pattern, txt):
            return level
    return ''


def extract_industries(text: str, max_items: int = 3) -> str:
    """
    Finds up to max_items industries based on keyword matching.
    """
    found = []
    lower = text.lower()
    for kw, industry in industries_map.items():
        if kw in lower and industry not in found:
            found.append(industry)
        if len(found) == max_items:
            break
    return ','.join(found)

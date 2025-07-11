import os
import time
import logging
import io
import csv
from typing import List, Dict
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY environment variable")

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

# Model settings
MODEL = "gemini-2.0-flash"
MAX_RETRIES = 1
RETRY_DELAY = 2  # seconds between retries

# Fields to extract (in order)
FIELDS = [
    'title', 'company', 'city', 'country',
    'officeType', 'experienceLevel', 'employmentType',
    'industries', 'visa', 'benefits', 'skills',
    'currency', 'salaryLow', 'salaryHigh'
]

# Prompt template for each job description
PROMPT_TEMPLATE = """
IMPORTANT:
- Provide exactly one line of valid CSV per job. Do not output any additional lines or separators.
- Include all 15 fields in this exact order on a single line:
  1. title (this is the title of the job and this is a required, if the title contains a comma then you have to enclose the whole title in " " for example "Manager, Direct Tax (Indian Tax))
  2. company (this is the company which posted the job listing, this is required)
  3. city (this is the city in which the job is required)
  4. country(this is the country in which the job city exists, if the country is not given then you can just put the country name based on your understanding i.e if the city name is Bangalore then you know the country will be India and so on)
  5. officeType (choose only one from these four options: Remote, Hybrid, In-Office, Remote-Anywhere, if not mentioned in the job description then choose Hybrid as default) 
  6. experienceLevel (choose any one from these six options: Intern, Entry-Level, Associate/Mid-Level, Senior-Level, Managerial, Executive, if not mentioned in the job then try to deduce on your based on the number of years the job description is asking for the job)
  7. employmentType (choose only one from these five options: Full-Time, Part-Time, Contract, Freelance, Temporary, if not mentioned in the job description then choose Full-Time as default)
  8. industries (list maximum 3 items and minimum one based on the job description; if containing commas, enclose in double quotes, for example if you deduce that a job comes in both Tech and Finance industry then you should return "Tech, Finance" and if you deduce that a role is simply a role in Tech industry then you should return Tech without any quotes. if it is not mentioned in the job description then try to deduce it by looking at the job description.)
  9. visa (Yes or No, either answer with a Yes or answer with a No, if you can't make sense of it from the job description then you can just choose No as a default)
  10. benefits (if containing commas, enclose in double quotes, make sure that these benefits are 3-4 items only and each item to be 1-2 words long only, for example "Health Insurance, Paid Leave, Flexible Hours", if you can't make it from the job description just leave it blank)
  11. skills (list 5–6 items; if containing commas, enclose in double quotes, for example "Python, Rust, Docker" or "Financial Auditing, PowerBI, Agile", you can't leave this blank)
  12. currency (symbol only, e.g., $, ₹, try to deduce the currency based on the city/country of the job posting for example if the job description mentions that the job is in New York then you already know you have to use the $ and if it's in somewhere in Germany then use the euro currency symbol)
  13. salaryLow(if this is not mentioned, you can leave it blank)
  14. salaryHigh(if this is not mentioned, you can leave it blank)
  15. j/i (i for internships; j for all other roles, you can't leave this blank, if you can't deduce from the job description choose j as default)
- Even if a field is blank, include it as an empty field (use ,, with nothing between).
- Use commas only to separate the 15 fields; fields containing commas must be enclosed in double quotes.

Example of a single valid CSV line:
AI Intern,Cognizant,Kolkata,India,Hybrid,Intern,Full-Time,"Tech,Consulting",,"Health Insurance,Paid Leave","Python,Rust,Neural Networks",₹,,,i


Job Description:
{description}
"""


def _stub_parse_batch(texts: List[str], urls: List[str], jis: List[int]) -> List[Dict]:
    """
    Fallback stub: returns dummy records when parsing fails.
    """
    records = []
    for text, url, ji in zip(texts, urls, jis):
        rec = {field: '' for field in FIELDS}
        rec.update({
            'title': 'Dummy Title',
            'company': 'Dummy Company',
            'city': 'Dummy City',
            'country': 'Dummy Country',
            'officeType': 'Remote',
            'experienceLevel': 'Entry-Level',
            'employmentType': 'Full-Time',
            'industries': 'Tech,Healthcare,Marketing',
            'visa': 'Yes',
            'benefits': '',
            'skills': '',
            'currency': '$',
            'salaryLow': '50000',
            'salaryHigh': '60000'
        })
        rec['url'] = url
        exp_level = rec.get('experienceLevel', '')
        rec['j/i'] = 'i' if exp_level.lower().startswith('intern') else 'j'
        records.append(rec)
    return records


def parse_batch(texts: List[str], urls: List[str], jis: List[int]) -> List[Dict]:
    """
    Parse job descriptions via Gemini Flash API into structured records.
    Falls back to stub on errors or format mismatches.
    """
    if not (len(texts) == len(urls) == len(jis)):
        raise ValueError("texts, urls, and jis must have the same length")

    # Build combined prompt
    prompts = [PROMPT_TEMPLATE.format(description=desc) for desc in texts]
    combined_prompt = "\n---\n".join(prompts)

    # Call Gemini with retries
    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.info(f"Sending request to Gemini (attempt {attempt+1})")
            response = client.models.generate_content(
                model=MODEL,
                contents=combined_prompt
            )
            content = response.text.strip()
            logger.info("Raw Gemini response:\n%s", content)
            break
        except Exception as e:
            logger.warning(f"Gemini request failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            logger.error("Max retries reached. Using stub parser.")
            return _stub_parse_batch(texts, urls, jis)

    # Process output lines
    lines = [l for l in content.splitlines() if l.strip()]
    records: List[Dict] = []
    expected_fields = len(FIELDS) + 1  # +1 for j/i

    for idx, (line, url, ji_idx) in enumerate(zip(lines, urls, jis)):
        # Parse CSV respecting quotes
        try:
            parts = next(csv.reader(io.StringIO(line)))
        except Exception as e:
            logger.warning(f"CSV parse failed on line {idx+1}: {e}")
            return _stub_parse_batch(texts, urls, jis)

        if len(parts) < expected_fields:
            logger.warning(f"Line {idx+1} has {len(parts)} fields (< expected {expected_fields}): {parts}")
            return _stub_parse_batch(texts, urls, jis)
        if len(parts) > expected_fields:
            logger.warning(f"Line {idx+1} has {len(parts)} fields (> expected {expected_fields}); extra fields will be ignored: {parts}")

        # Map fields to values (ignore extras)
        rec: Dict[str, str] = {field: parts[i] for i, field in enumerate(FIELDS)}
        rec['url'] = url
        rec['j/i'] = parts[expected_fields - 1]
        records.append(rec)

    return records

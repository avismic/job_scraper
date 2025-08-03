import os
import time
import logging
import io
import csv
import threading
from typing import List, Dict
from google import genai
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

MODEL        = "gemini-2.5-flash"
MAX_RETRIES  = 1          
RETRY_DELAY  = 2          

CPM           = int(os.getenv("GEMINI_CPM", "30"))
MIN_INTERVAL  = 60.0 / CPM
_last_call    = 0.0
_rate_lock    = threading.Lock()

FIELDS = [
    'title','company','city','country',
    'officeType','experienceLevel','employmentType',
    'industries','visa','benefits','skills',
    'currency','salaryLow','salaryHigh'
]

PROMPT_TEMPLATE = """
IMPORTANT:
- Provide exactly one line of valid CSV per job. Do not output any additional lines or separators.
- Include all 15 fields in this exact order on a single line:
  1. title (this is the title of the job and this is a required, if the title contains a comma then you have to enclose the whole title in " " for example "Manager, Direct Tax (Indian Tax))
  2. company (this is the company which posted the job listing, this is required)
  3. city (this is the city in which the job is required, you can't leave this empty)
  4. country(this is the country in which the job city exists, if the country is not given then you can just put the country name based on your understanding i.e if the city name is Bangalore then you know the country will be India and so on)
  5. officeType (choose only one from these four options: Remote, Hybrid, In-Office, Remote-Anywhere, if not mentioned in the job description then choose Hybrid as default) 
  6. experienceLevel (choose any one from these six options: Intern, Entry-Level, Associate/Mid-Level, Senior-Level, Managerial, Executive, if not mentioned in the job then try to deduce on your based on the number of years the job description is asking for the job, like if the experience required is 0-2 years then it should be tagged as an Entry-Level job)
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
def _stub_parse_batch() -> List[Dict]:
    """Return empty list instead of dummy placeholders."""
    return []

def parse_batch(texts: List[str], urls: List[str], jis: List[int]) -> List[Dict]:
    """
    • Sends a batch to Gemini.
    • Parses each CSV line individually.
    • Keeps well-formed rows; skips malformed ones.
    • Retries once on API error or if zero rows were valid.
    """
    if not (len(texts) == len(urls) == len(jis)):
        raise ValueError("texts, urls and jis must be same length")

    global _last_call       

    combined_prompt = "\n---\n".join(
        PROMPT_TEMPLATE.format(description=d) for d in texts
    )
    expected_fields = len(FIELDS) + 1  

    for attempt in range(MAX_RETRIES + 1):
        with _rate_lock:
            now   = time.time()
            delta = now - _last_call
            if delta < MIN_INTERVAL:
                wait = MIN_INTERVAL - delta
                logger.info(f"Throttling Gemini for {wait:.2f}s to respect {CPM} CPM")
                time.sleep(wait)
            _last_call = time.time()

        try:
            logger.info(f"Gemini call attempt {attempt+1}")
            resp    = client.models.generate_content(
                model=MODEL,
                contents=combined_prompt
            )
            content = resp.text.strip()
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return _stub_parse_batch()

        valid_records: List[Dict] = []
        lines = [l for l in content.splitlines() if l.strip()]

        if len(lines) == 0:
            logger.warning("Gemini returned 0 lines")

        for idx, (line, url, ji) in enumerate(zip(lines, urls, jis)):
            try:
                parts = next(csv.reader(io.StringIO(line)))
                if len(parts) != expected_fields:
                    raise ValueError(f"{len(parts)} fields (need {expected_fields})")
                rec = {field: parts[i] for i, field in enumerate(FIELDS)}
                rec['url'] = url
                rec['j/i'] = parts[-1]
                valid_records.append(rec)
            except Exception as e:
                logger.warning(f"Line {idx+1} malformed → skipped ({e})")

        if valid_records:          
            return valid_records

        logger.warning("All rows malformed; retrying…")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return _stub_parse_batch()

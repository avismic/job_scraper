import os
import time
import logging
import json
from typing import List, Dict
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY environment variable")

# Initialize client
genai_client = genai.Client(api_key=API_KEY)

# Model settings
MODEL = "gemini-2.0-flash"
MAX_RETRIES = 1
RETRY_DELAY = 2  # seconds

# Expected schema fields
SCHEMA_FIELDS = [
    'title', 'company', 'city', 'country',
    'officeType', 'experienceLevel', 'employmentType',
    'industries', 'visa', 'benefits', 'skills',
    'currency', 'salaryLow', 'salaryHigh'
]

# Stub parser for fallback

def _stub_parse_batch(texts: List[str], urls: List[str], jis: List[int]) -> List[Dict]:
    records = []
    for text, url, ji in zip(texts, urls, jis):
        rec = {field: '' for field in SCHEMA_FIELDS}
        rec.update({
            'title':'Dummy Title',
            'company':'Dummy Company',
            'city':'Dummy City',
            'country':'Dummy Country',
            'officeType':'Remote',
            'experienceLevel':'Entry-Level',
            'employmentType':'Full-Time',
            'industries':'Tech,Healthcare,Marketing',
            'visa':'Yes',
            'benefits':'Health insurance',
            'skills':'Python,Rust,Excel',
            'currency':'$',
            'salaryLow':'50000',
            'salaryHigh':'60000'
        })
        rec['url'] = url
        rec['j/i'] = 'i' if rec['experienceLevel'].lower().startswith('intern') else 'j'
        records.append(rec)
    return records

# JSON-based parser
def parse_batch(texts: List[str], urls: List[str], jis: List[int]) -> List[Dict]:
    """
    For each job description, call Gemini to return a JSON object matching SCHEMA_FIELDS,
    then post-process into flat dicts, appending URL and j/i flag.
    Falls back to stub on errors.
    """
    records: List[Dict] = []
    if not (len(texts) == len(urls) == len(jis)):
        raise ValueError("texts, urls, and jis must have the same length")

    for desc, url, ji in zip(texts, urls, jis):
        prompt = (
            "Extract the following fields from the job description as JSON only, no extra text.\n"
            f"Fields: {', '.join(SCHEMA_FIELDS)}\n"
            "Industries and skills should be JSON arrays of strings.\n"
            "Example output: {\"title\": \"...\", ...}\n"
            "Job Description:\n" + desc
        )
        # call with retries
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.info(f"Gemini JSON call (attempt {attempt+1})")
                res = genai_client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )
                text = res.text.strip()

                # Strip markdown fences if present
                if text.startswith("```"):
                    lines = text.splitlines()
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    text = "\n".join(lines).strip()

                logger.info("Raw JSON response: %s", text)
                data = json.loads(text)
                break
            except Exception as e:
                logger.warning(f"JSON parse error or API failure: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                logger.error("Falling back to stub JSON parser")
                data = _stub_parse_batch([desc],[url],[ji])[0]
                break

        # Post-process
        rec: Dict[str, str] = {}
        for field in SCHEMA_FIELDS:
            val = data.get(field, '')
            if isinstance(val, list):
                val = ','.join(val)
            rec[field] = str(val) if val is not None else ''
        rec['url'] = url
        rec['j/i'] = 'i' if rec['experienceLevel'].lower().startswith('intern') else 'j'
        records.append(rec)

    return records

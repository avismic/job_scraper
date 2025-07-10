import os
import csv
import tempfile
import requests
import pandas as pd
import streamlit as st
import logging

from scraper.schema_extractor import extract_jobposting_schema
from scraper.static_scraper import scrape as static_scrape
from scraper.dynamic_scraper import scrape as dynamic_scrape
from scraper.link_extractor import extract_links
from gemini.parser import parse_batch
from utils.validators import validate_record
from utils.heuristics import (
    extract_salary,
    extract_office_type,
    extract_experience_level,
    extract_industries,
)

# Configure logging for fallback defaults
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.WARNING
)
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 5
FIELDNAMES = [
    'title','company','city','country',
    'officeType','experienceLevel','employmentType',
    'industries','visa','benefits','skills',
    'url','j/i','currency','salaryLow','salaryHigh'
]

# Default fallbacks for missing fields
FALLBACK_DEFAULTS = {
    'visa': 'No',
    'employmentType': 'Full-Time',
    'officeType': 'In-Office',
    'experienceLevel': 'Entry-Level',
    'industries': 'Tech',  # default to first industry
}

# Helper: apply defaults and log
def apply_fallbacks(rec: dict, url: str):
    for field, default in FALLBACK_DEFAULTS.items():
        if not rec.get(field):
            logger.warning(f"Missing '{field}' for {url}, defaulting to '{default}'")
            rec[field] = default

st.set_page_config(page_title="Job Scraper", layout="wide")
st.title("🧾 Career Page Job Scraper")

# 1. File Upload
uploaded = st.file_uploader("Upload your CSV (must have a 'url' column)", type="csv")
if not uploaded:
    st.stop()
df_in = pd.read_csv(uploaded)
if 'url' not in df_in.columns:
    st.error("Input CSV must contain a 'url' column.")
    st.stop()
urls = df_in['url'].dropna().unique().tolist()
st.success(f"Found {len(urls)} unique URLs.")

# 2. Run Scrape & Parse
if st.button("Run Scraper"):
    # Temp files
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp_txt.close(); tmp_csv.close()

    # Prepare writer
    out_f = open(tmp_csv.name, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
    writer.writeheader()

    progress = st.progress(0)
    batch = []
    total = len(urls)

    for idx, url in enumerate(urls, start=1):
        st.write(f"🔍 [{idx}/{total}] Processing: {url}")

        # 2a. Expand career homepages
        if st.checkbox(f"▶️ Expand links on {url}", key=idx):
            try:
                sub_urls = extract_links(url)
                st.write(f" • Found {len(sub_urls)} links")
            except Exception as e:
                st.warning(f" • Link extraction failed: {e}")
                sub_urls = []
        else:
            sub_urls = [url]

        # 2b. Process each job URL
        for u in sub_urls:
            # JSON-LD schema extraction
            try:
                resp = requests.get(u, timeout=10)
                html = resp.text
            except Exception as e:
                st.warning(f" • Failed to fetch {u}: {e}")
                html = ""
            schema_rec = extract_jobposting_schema(u, html)

            if schema_rec:
                rec = {}
                for f in FIELDNAMES:
                    if f in schema_rec:
                        rec[f] = schema_rec[f]
                    elif f == 'url':
                        rec[f] = u
                    elif f == 'j/i':
                        exp = schema_rec.get('experienceLevel','')
                        rec[f] = 'i' if exp.lower().startswith('intern') else 'j'
                    else:
                        rec[f] = ''
                apply_fallbacks(rec, u)
                writer.writerow(rec)
                continue

            # Fallback: scrape text
            try:
                text = static_scrape(u)
                if not text or len(text) < 200:
                    text = dynamic_scrape(u)
            except Exception as e:
                st.warning(f" • Scrape failed for {u}: {e}")
                text = ""

            # Heuristic extraction
            cur, low, high = extract_salary(text)
            office = extract_office_type(text)
            exp_level = extract_experience_level(text)
            industries = extract_industries(text)
            if any([cur, low, high, office, exp_level, industries]):
                rec = {f: '' for f in FIELDNAMES}
                rec.update({
                    'currency': cur,
                    'salaryLow': low,
                    'salaryHigh': high,
                    'officeType': office,
                    'experienceLevel': exp_level,
                    'industries': industries,
                    'url': u,
                    'j/i': 'i' if exp_level.lower().startswith('intern') else 'j',
                })
                apply_fallbacks(rec, u)
                writer.writerow(rec)
                continue

            # Batch for AI
            batch.append({'text': text, 'url': u, 'j/i': idx})
            if len(batch) == BATCH_SIZE:
                st.write(f"💬 Parsing batch of {BATCH_SIZE}")
                recs = parse_batch(
                    [b['text'] for b in batch],
                    [b['url'] for b in batch],
                    [b['j/i'] for b in batch],
                )
                clean = [validate_record(r) for r in recs]
                for r in clean:
                    apply_fallbacks(r, u)
                    writer.writerow(r)
                batch = []
                progress.progress(idx / total)

    # Final batch
    if batch:
        st.write(f"💬 Parsing final batch of {len(batch)}")
        recs = parse_batch(
            [b['text'] for b in batch],
            [b['url'] for b in batch],
            [b['j/i'] for b in batch],
        )
        clean = [validate_record(r) for r in recs]
        for r in clean:
            apply_fallbacks(r, u)
            writer.writerow(r)

    out_f.close()

    # 3. Display & Download
    st.success("✅ Scraping & parsing complete!")
    df_out = pd.read_csv(tmp_csv.name)
    st.dataframe(df_out)

    st.download_button(
        label="📥 Download Results",
        data=open(tmp_csv.name, 'rb').read(),
        file_name="jobs_output.csv",
        mime="text/csv"
    )
    st.write("---")
    st.download_button(
        label="📥 Download Raw Batches (txt)",
        data=open(tmp_txt.name, 'rb').read(),
        file_name="raw_batches.txt",
        mime="text/plain"
    )

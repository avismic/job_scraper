import sys
if sys.platform.startswith("win"):
    import asyncio
    # Use the SelectorEventLoop on Windows so create_subprocess_exec is supported
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import csv
import tempfile

import pandas as pd
import streamlit as st

from scraper.static_scraper import scrape as static_scrape
from scraper.dynamic_scraper import scrape as dynamic_scrape
from scraper.link_extractor import extract_links
from gemini.parser import parse_batch
from utils.validators import validate_record

# Constants
BATCH_SIZE = 10

st.set_page_config(page_title="Job Scraper", layout="wide")
st.title("🧾 Career Page Job Scraper")

# --- 1. Get list of job URLs, either via a careers‐page URL or an uploaded CSV ---

# Option A: user enters a single careers page URL
careers_page = st.text_input(
    "Or enter a main careers page URL to auto-discover all job postings:",
    placeholder="https://www.company.com/careers"
)

urls = None

if careers_page:
    # If they've typed a URL, attempt to extract links immediately
    try:
        urls = extract_links(careers_page)
        st.success(f"✅ Discovered {len(urls)} job posting URLs from `{careers_page}`")
    except Exception as e:
        st.error(f"Failed to extract job links from `{careers_page}`: {e}")
        st.stop()

# Option B: fall back to the CSV uploader if no careers page URL was provided
elif not careers_page:
    uploaded = st.file_uploader("Upload your CSV (must have a column 'url')", type="csv")
    if not uploaded:
        st.info("Please upload a CSV or enter a careers page URL above.")
        st.stop()

    df_in = pd.read_csv(uploaded)
    if 'url' not in df_in.columns:
        st.error("Input CSV must contain a column named `url`.")
        st.stop()

    urls = df_in['url'].dropna().unique().tolist()
    st.success(f"✅ Loaded {len(urls)} unique URLs from CSV")

# At this point, `urls` holds all job-posting URLs to process
total = len(urls)

# --- 2. Run Scrape & Parse ---
if st.button("Run Scraper"):
    # Prepare temporary files for raw batches and final CSV
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp_txt.close()
    tmp_csv.close()

    # Set up CSV writer for validated output
    fieldnames = [
        'title', 'company', 'city', 'country', 'officeType', 'experienceLevel',
        'employmentType', 'industries', 'visa', 'benefits', 'skills', 'url', 'j/i',
        'currency', 'salaryLow', 'salaryHigh'
    ]
    out_f = open(tmp_csv.name, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()

    progress = st.progress(0.0)
    batch = []

    for idx, url in enumerate(urls, start=1):
        st.write(f"🔍 [{idx}/{total}] Processing {url}")

        # Optional: allow re-expansion of any link (legacy checkbox)
        if st.checkbox(f"▶️ Expand links on {url}", key=f"expand_{idx}"):
            try:
                sub_urls = extract_links(url)
                st.write(f"    • Found {len(sub_urls)} sub-URLs")
            except Exception as e:
                st.warning(f"    • Link extraction failed for {url}: {e}")
                sub_urls = []
        else:
            sub_urls = [url]

        # Scrape each individual job URL
        for u in sub_urls:
            try:
                text = static_scrape(u)
                # fallback to dynamic if too little content
                if not text or len(text) < 200:
                    text = dynamic_scrape(u)
                status = "✔️"
            except Exception as e:
                st.warning(f"    ⚠️ Scrape failed for {u}: {e}")
                text = ""
                status = "⚠️"

            batch.append({'text': text, 'url': u, 'j/i': idx})

            # When batch is full, send to Gemini for parsing
            if len(batch) == BATCH_SIZE:
                st.write(f"💬 Parsing batch of {BATCH_SIZE}")
                recs = parse_batch(
                    [b['text'] for b in batch],
                    [b['url'] for b in batch],
                    [b['j/i'] for b in batch],
                )
                cleaned = [validate_record(r) for r in recs]
                for r in cleaned:
                    writer.writerow(r)
                batch = []
                progress.progress(idx / total)

    # Handle final partial batch
    if batch:
        st.write(f"💬 Parsing final batch of {len(batch)}")
        recs = parse_batch(
            [b['text'] for b in batch],
            [b['url'] for b in batch],
            [b['j/i'] for b in batch],
        )
        cleaned = [validate_record(r) for r in recs]
        for r in cleaned:
            writer.writerow(r)

    out_f.close()

    # --- 3. Display & Download Results ---
    st.success("✅ Scraping & parsing complete!")
    df_out = pd.read_csv(tmp_csv.name)
    st.dataframe(df_out, use_container_width=True)

    st.download_button(
        label="📥 Download Results CSV",
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

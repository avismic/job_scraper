import sys
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import csv
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed  # ➜ added

import pandas as pd
import streamlit as st

from scraper.static_scraper import scrape as static_scrape
from scraper.dynamic_scraper import scrape as dynamic_scrape
from scraper.link_extractor import extract_links
from gemini.parser import parse_batch
from utils.validators import validate_record

# ---------- Tunable constants ----------
BATCH_SIZE   = 10   # how many job descriptions per Gemini call
MAX_WORKERS  = 10    # how many Gemini calls in parallel  ➜ added

st.set_page_config(page_title="Job Scraper", layout="wide")
st.title("🧾 Career Page Job Scraper")

# --- 1. Collect job-posting URLs ------------------------------------------------
careers_page = st.text_input(
    "Or enter a main careers page URL to auto-discover all job postings:",
    placeholder="https://www.company.com/careers"
)

urls = None
if careers_page:
    try:
        urls = extract_links(careers_page)
        st.success(f"✅ Discovered {len(urls)} job posting URLs from `{careers_page}`")
    except Exception as e:
        st.error(f"Failed to extract job links from `{careers_page}`: {e}")
        st.stop()
else:
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

total = len(urls)

# --- 2. Scrape, batch & parse ---------------------------------------------------
if st.button("Run Scraper"):
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp_txt.close()
    tmp_csv.close()

    fieldnames = [
        'title', 'company', 'city', 'country', 'officeType', 'experienceLevel',
        'employmentType', 'industries', 'visa', 'benefits', 'skills', 'url', 'j/i',
        'currency', 'salaryLow', 'salaryHigh'
    ]
    out_f = open(tmp_csv.name, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()

    progress = st.progress(0.0)
    batch, futures = [], []

    # Thread pool for parallel Gemini calls  ➜ added
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    for idx, url in enumerate(urls, start=1):
        st.write(f"🔍 [{idx}/{total}] Processing {url}")

        # (optional) re-expand links checkbox – unchanged
        if st.checkbox(f"▶️ Expand links on {url}", key=f"expand_{idx}"):
            try:
                sub_urls = extract_links(url)
                st.write(f"    • Found {len(sub_urls)} sub-URLs")
            except Exception as e:
                st.warning(f"    • Link extraction failed for {url}: {e}")
                sub_urls = []
        else:
            sub_urls = [url]

        # scrape each job URL
        for u in sub_urls:
            try:
                text = static_scrape(u)
                if not text or len(text) < 200:
                    text = dynamic_scrape(u)
            except Exception as e:
                st.warning(f"    ⚠️ Scrape failed for {u}: {e}")
                text = ""
            batch.append({'text': text, 'url': u, 'j/i': idx})

            # submit batch to Gemini when full
            if len(batch) == BATCH_SIZE:
                fut = executor.submit(
                    parse_batch,
                    [b['text'] for b in batch],
                    [b['url']  for b in batch],
                    [b['j/i']  for b in batch],
                )
                futures.append(fut)
                batch = []
                progress.progress(min(1.0, idx / total))

    # final partial batch
    if batch:
        fut = executor.submit(
            parse_batch,
            [b['text'] for b in batch],
            [b['url']  for b in batch],
            [b['j/i']  for b in batch],
        )
        futures.append(fut)

    # gather results as they finish  ➜ added
    completed = 0
    for fut in as_completed(futures):
        recs = fut.result()
        cleaned = [validate_record(r) for r in recs]
        for r in cleaned:
            writer.writerow(r)
        completed += 1
        progress.progress(min(1.0, completed / len(futures)))

    out_f.close()
    executor.shutdown(wait=True)

    # --- 3. Display & Download ---------------------------------------------------
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

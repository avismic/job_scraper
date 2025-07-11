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
BATCH_SIZE = 5

st.set_page_config(page_title="Job Scraper", layout="wide")

st.title("🧾 Career Page Job Scraper")

# 1. File Uploader
uploaded = st.file_uploader("Upload your CSV (must have a column 'url')", type="csv")
if not uploaded:
    st.stop()

# Read URLs
df_in = pd.read_csv(uploaded)
if 'url' not in df_in.columns:
    st.error("Input CSV must contain a 'url' column.")
    st.stop()

urls = df_in['url'].dropna().unique().tolist()
st.success(f"Found {len(urls)} unique URLs.")

# 2. Run Scrape & Parse
if st.button("Run Scraper"):
    # Temporary files
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_csv = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp_txt.close()
    tmp_csv.close()

    # Prepare output CSV writer
    fieldnames = [
        'title','company','city','country','officeType','experienceLevel',
        'employmentType','industries','visa','benefits','skills','url','j/i',
        'currency','salaryLow','salaryHigh'
    ]
    out_f = open(tmp_csv.name, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    writer.writeheader()

    progress = st.progress(0)
    batch = []
    total = len(urls)

    for idx, url in enumerate(urls, 1):
        st.write(f"🔍 [{idx}/{total}] Processing {url}")
        # 2a. If it’s a career homepage, expand links
        if st.checkbox(f"▶️ Expand links on {url}", key=idx):
            try:
                sub_urls = extract_links(url)
                st.write(f" • Found {len(sub_urls)} job links")
            except Exception as e:
                st.warning(f" • Link extraction failed: {e}")
                sub_urls = []
        else:
            sub_urls = [url]

        # 2b. Scrape each link
        for u in sub_urls:
            try:
                text = static_scrape(u)
                if not text or len(text) < 200:
                    # fallback to dynamic if too little content
                    text = dynamic_scrape(u)
                status = "✔️"
            except Exception as e:
                st.warning(f" • Scrape failed for {u}: {e}")
                text = ""
                status = "⚠️"
            batch.append({'text': text, 'url': u, 'j/i': idx})

            # Process batch
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

    # Final smaller batch
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

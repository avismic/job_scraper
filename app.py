import sys, os
print("PYTHONPATH:", sys.path)
print("Exists scraper/static_scraper.py?", os.path.exists("scraper/static_scraper.py"))

import requests
from scraper.schema_extractor import extract_jobposting_schema

resp = requests.get(url, timeout=10)
html = resp.text
schema_rec = extract_jobposting_schema(url, html)

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed 
from scraper.static_scraper import scrape
from gemini.parser import parse_batch
from utils.validators import validate_record

BATCH_SIZE   = 10
MAX_WORKERS  = 10                    
TEMP_TXT     = 'data/temp_output.txt'

def read_urls(input_csv):
    urls = []
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'url' not in reader.fieldnames:
            print("Error: input CSV must have a 'url' column")
            sys.exit(1)
        for row in reader:
            urls.append(row['url'])
    return urls


def append_to_txt(lines):
    os.makedirs(os.path.dirname(TEMP_TXT), exist_ok=True)
    mode = 'a' if os.path.exists(TEMP_TXT) else 'w'
    with open(TEMP_TXT, mode, encoding='utf-8') as f:
        for line in lines:
            f.write(line.strip() + '\n')


def records_to_csv(records, output_csv):
    fieldnames = [
        'title', 'company', 'city', 'country', 'officeType', 'experienceLevel',
        'employmentType', 'industries', 'visa', 'benefits', 'skills', 'url', 'j/i',
        'currency', 'salaryLow', 'salaryHigh'
    ]
    write_header = not os.path.exists(output_csv)
    with open(output_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def main():
    if len(sys.argv) != 3:
        print("Usage: python app.py input.csv output.csv")
        sys.exit(1)
    input_csv, output_csv = sys.argv[1], sys.argv[2]

    urls     = read_urls(input_csv)
    batch    = []
    futures  = []

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS) 

    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{len(urls)}] Scraping {url}...")
        try:
            text = scrape(url)
        except Exception as e:
            print(f"  ⚠️ Warning: could not scrape {url}: {e}")
            text = ""
        batch.append({'text': text, 'url': url, 'j/i': idx})

        if len(batch) == BATCH_SIZE:
            texts = [b['text'] for b in batch]
            urls_b = [b['url'] for b in batch]
            jis   = [b['j/i'] for b in batch]

            fut = executor.submit(parse_batch, texts, urls_b, jis) 
            futures.append(fut)
            batch = []

    if batch:
        texts = [b['text'] for b in batch]
        urls_b = [b['url'] for b in batch]
        jis   = [b['j/i'] for b in batch]
        futures.append(executor.submit(parse_batch, texts, urls_b, jis))

    for fut in as_completed(futures):                                
        parsed  = fut.result()
        cleaned = [validate_record(r) for r in parsed]

        lines = [
            ','.join(str(clean_rec[field]) for field in cleaned_rec.keys())
            for cleaned_rec in cleaned
        ]
        append_to_txt(lines)
        records_to_csv(cleaned, output_csv)

    executor.shutdown(wait=True)  

    print(f"\n✅ Done.")
    print(f"  • Final CSV → {output_csv}")
    print(f"  • Raw batches → {TEMP_TXT}")


if __name__ == '__main__':
    main()

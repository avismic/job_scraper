import logging
logging.basicConfig(level=logging.INFO)

from gemini.parser import parse_batch

# 1) Enable INFO-level logs so we see any Gemini activity
logging.basicConfig(level=logging.INFO)
print("🏃 Running test_parse…")

# 2) Load your sample JD text
try:
    with open("sample_job.txt", encoding="utf-8") as f:
        text = f.read().strip()
except FileNotFoundError:
    print("❌ sample_job.txt not found. Make sure it’s in this folder alongside test_parse.py.")
    exit(1)

if not text:
    print("❌ sample_job.txt is empty. Paste in some real job description text.")
    exit(1)

print(f"📄 Sample length: {len(text)} characters\n")

# 3) Call your parser
records = parse_batch([text], ["https://example.com/sample-job"], [1])

# 4) Print out exactly what was returned
print("✅ parse_batch returned:")
for rec in records:
    for k, v in rec.items():
        print(f"  {k}: {v}")
    print("—")

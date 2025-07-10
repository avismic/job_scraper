import logging
from gemini.parser import parse_batch

# Enable INFO-level logging so we see Gemini calls and any warnings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1) Load your sample text
try:
    with open("sample_job.txt", encoding="utf-8") as f:
        text = f.read().strip()
except FileNotFoundError:
    print("❌ sample_job.txt not found. Make sure it exists and you’re in the right folder.")
    exit(1)

if not text:
    print("❌ sample_job.txt is empty. Paste some real job description text into it.")
    exit(1)

print("📄 Sample JD (first 300 chars):")
print(text[:300].replace("\n"," ") + "…\n")

# 2) Call parse_batch on a single‐item list
records = parse_batch([text], ["https://careers.ey.com/ey/job/Kochi-Travel-Manager-India-GDS-KL-682303/1213890701/"], [1])

# 3) Show the parsed result
print("✅ Parsed record:")
for k, v in records[0].items():
    print(f"  {k}: {v}")

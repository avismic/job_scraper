import os
import sys

print("📁 Working directory:", os.getcwd())
print("📂 Files here:", os.listdir())
print("✅ sample_job.txt exists?", os.path.exists("sample_job.txt"))
print("✅ gemini/parser.py exists?", os.path.exists(os.path.join("gemini","parser.py")))
print("🛣️ Python path entries:")
for p in sys.path:
    print("   ", p)

try:
    from gemini.parser import parse_batch
    print("✅ Imported parse_batch from gemini.parser")
except Exception as e:
    print("❌ Importing parse_batch failed:", e)

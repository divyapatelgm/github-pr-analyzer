# ============================================================
# V2 STEP 1: STRICT SCHEMA VALIDATION
# ============================================================
import json
import sys

if len(sys.argv) > 1:
    NEW_DATASET_PATH = sys.argv[1]
else:
    NEW_DATASET_PATH = "path/to/your/new_140k_dataset.jsonl"  # <-- UPDATE THIS

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records

print(f"Loading new dataset from {NEW_DATASET_PATH}...")
try:
    raw_dataset = load_jsonl(NEW_DATASET_PATH)
except FileNotFoundError:
    print(f"File not found: {NEW_DATASET_PATH}")
    sys.exit(1)
    
print(f"Loaded {len(raw_dataset):,} raw records.\n")

print("=" * 75)
print("STEP 0: FLATTENING")
print("=" * 75)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.flattener import Flattener

flattener = Flattener()
new_dataset = flattener.flatten(raw_dataset)
print(f"Successfully flattened {len(new_dataset):,} records.\n")

EXPECTED_KEYS = {"id", "repo_name", "programming_language", "input", "output", "system_prompt"}
first_record_keys = set(new_dataset[0].keys())

print("=" * 75)
print("SCHEMA VALIDATION")
print("=" * 75)
print(f"Expected keys : {sorted(EXPECTED_KEYS)}")
print(f"Actual keys   : {sorted(first_record_keys)}")

missing_keys = EXPECTED_KEYS - first_record_keys
extra_keys = first_record_keys - EXPECTED_KEYS

if missing_keys:
    print(f"\n[MISSING] Expected keys not found: {missing_keys}")
if extra_keys:
    print(f"\n[EXTRA] Unexpected additional keys found: {extra_keys}")

assert not missing_keys, f"Schema mismatch! Missing required keys: {missing_keys}."

print("\n[PASS] First record schema matches expected structure.\n")

inconsistent_records = []
for i, record in enumerate(new_dataset):
    if set(record.keys()) != first_record_keys:
        inconsistent_records.append((i, set(record.keys())))
        if len(inconsistent_records) >= 20:
            break

if inconsistent_records:
    print(f"[WARNING] {len(inconsistent_records)}+ records have a different key set:")
    for idx, keys in inconsistent_records[:10]:
        print(f"  Record {idx}: {sorted(keys)}")
else:
    print("[PASS] All records have consistent schema (checked full dataset).")

missing_counts = {"input": 0, "output": 0, "system_prompt": 0}
for record in new_dataset:
    for field in missing_counts:
        val = record.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing_counts[field] += 1

print("\n" + "=" * 75)
print("MISSING VALUE CHECK (core training fields)")
print("=" * 75)
for field, count in missing_counts.items():
    print(f"  {field:<20}: {count:,} missing / {len(new_dataset):,} total")

assert all(c == 0 for c in missing_counts.values()), "Missing values found — investigate before proceeding."

print("\n[PASS] No missing values in core training fields.")
print(f"\nSCHEMA VALIDATION COMPLETE — {len(new_dataset):,} records ready for V2 pipeline.")

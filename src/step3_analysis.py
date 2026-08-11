import json
from src.flattener import Flattener
from src.quality_filter import QualityFilter
import numpy as np

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records

print("Loading raw dataset...")
raw_data = load_jsonl("data/processed/master_dataset_v1.jsonl")

print("Flattening...")
flattener = Flattener()
flat_data = flattener.flatten(raw_data)

print("Running Token/Percentile Analysis (Step 3)...")
qf = QualityFilter()

lengths = []
for i, r in enumerate(flat_data):
    if i % 10000 == 0:
        print(f"Processed {i:,} / {len(flat_data):,} records for tokenization...")
    diff_len = qf._get_token_length(r.get('input', ''))
    comment_len = qf._get_token_length(r.get('output', ''))
    lengths.append(diff_len + comment_len)

if lengths:
    p90, p95, p99, p99_5, p99_9 = np.percentile(lengths, [90, 95, 99, 99.5, 99.9])
    print("\n" + "=" * 75)
    print("TOKEN LENGTH PERCENTILES (Qwen2.5-7B-Instruct with apply_chat_template padding)")
    print("=" * 75)
    print(f"  90th   : {p90:,.1f} tokens")
    print(f"  95th   : {p95:,.1f} tokens")
    print(f"  99th   : {p99:,.1f} tokens")
    print(f"  99.5th : {p99_5:,.1f} tokens")
    print(f"  99.9th : {p99_9:,.1f} tokens")
    print("=" * 75)
else:
    print("No lengths computed!")

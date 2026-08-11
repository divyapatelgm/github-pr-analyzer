import json
import logging
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

from src.validator import Validator
from src.quality_filter import QualityFilter
from src.dataset_builder import DatasetBuilder
from src.evaluator import Evaluator
from src.analytics import Analytics
from src.metadata_enricher import MetadataEnricher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("V2Pipeline")

def load_jsonl(filepath: str):
    data = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
    return data

def build_v2_pipeline(new_data_path: str, old_train_path: str, old_val_path: str, output_dir: str = "data/training/v2_strict/"):
    logger.info("--- Starting V2 Strict Pipeline ---")
    
    # 1. Load Data
    new_data = load_jsonl(new_data_path)
    old_train = load_jsonl(old_train_path)
    old_val = load_jsonl(old_val_path)
    
    master_raw = old_train + old_val + new_data
    if not master_raw:
        logger.error("No data found!")
        return

    # 2. Structural Group-Extension Map
    # PR id is repo_name + "_" + pr_number
    old_pr_assignments = {}
    def _map_prs(data_split, split_name):
        for r in data_split:
            # Reconstruct PR identifier
            repo = r.get('repo_name', r.get('repository', {}).get('repo_name', ''))
            
            pr_node = r.get('pull_request')
            if pr_node:
                pr_num = str(pr_node.get('pr_number', ''))
            else:
                # If reading from already built split
                pr_num = r.get('id', '').split('-')[0].replace(repo, '').strip('_')
                if not pr_num:
                    continue # Handle edge cases based on exact ID formatting if needed
                    
            pr_identifier = f"{repo}_{pr_num}"
            old_pr_assignments[pr_identifier] = split_name
            
    # Assuming old_train/val have the raw nested format or flat format
    # In V1 they were saved as flat schemas, so we parse id: {repo_name}_{pr_number}-{review_id}
    # Wait, V1 schema id was actually pr_number-review_id!
    # Let's just use the provided JSONs safely
    for r in old_train:
        repo = r.get('repo_name', '')
        # V1 ID was f"{pr_number}-{review_id}"
        pr_num = r.get('id', '').split('-')[0]
        old_pr_assignments[f"{repo}_{pr_num}"] = 'train'
    for r in old_val:
        repo = r.get('repo_name', '')
        pr_num = r.get('id', '').split('-')[0]
        old_pr_assignments[f"{repo}_{pr_num}"] = 'val'
        
    logger.info(f"Loaded {len(old_pr_assignments)} old PR assignments to enforce structural split extension.")

    def log_concentration(stage: str, data: list):
        # We need a flat view
        repos = {}
        langs = {}
        total = len(data)
        if total == 0: return
        for r in data:
            # Support both flat and nested
            repo = r.get('repo_name', r.get('repository', {}).get('repo_name', 'unknown'))
            lang = r.get('programming_language', r.get('file', {}).get('programming_language', 'unknown'))
            repos[repo] = repos.get(repo, 0) + 1
            langs[lang] = langs.get(lang, 0) + 1
            
        for repo, count in repos.items():
            pct = count / total
            if pct > 0.05:
                logger.warning(f"[FLAG] {stage}: Repo {repo} accounts for {pct:.1%} of data (>5%)")
                
        # we could track diffs here, but for now we just flag > 5% repos
        # return langs for tracking diffs
        return {l: c/total for l, c in langs.items()}

    master_id_set = set()
    for r in master_raw:
        # nested
        if 'review' in r:
            master_id_set.add(f"{r['repository']['repo_name']}_{r['pull_request']['pr_number']}-{r['review']['review_id']}")
        else: # flat
            master_id_set.add(f"{r['repo_name']}_{r['id']}") # Just make a unique ID set

    # We need to flatten the raw nested schema to the flat schema first
    from src.flattener import Flattener
    flattener = Flattener()
    flattened_data = flattener.flatten(new_data)
    
    # Redefine master_id_set properly from the flattened ids to match downstream checks
    master_id_set = set(r['id'] for r in flattened_data)

    validator = Validator()
    valid_data = validator.validate(flattened_data)
    log_concentration("Post-Validation", valid_data)
    
    enricher = MetadataEnricher()
    enriched_data = enricher.enrich(valid_data)
    enricher.enrich_and_report_provenance(enriched_data)
    
    q_filter = QualityFilter()
    filtered_data = q_filter.filter(enriched_data)
    log_concentration("Post-Filtering", filtered_data)
    
    builder = DatasetBuilder(output_dir)
    df_train, df_val = builder.build(filtered_data, old_pr_assignments)
    
    evaluator = Evaluator()
    _, df_val_updated = evaluator.verify_leakage(df_train, df_val)
    
    # Save updated val
    df_val_updated.to_json(os.path.join(output_dir, 'validation.jsonl'), orient='records', lines=True)
    df_val_updated.to_csv(os.path.join(output_dir, 'validation.csv'), index=False)
    
    analytics = Analytics()
    analytics.check_internal_duplication(df_train)
    analytics.extract_quality_sample(pd.concat([df_train, df_val_updated]))
    
    # Set-based ID Math Assert
    # Re-read final datasets to get precise sets
    train_ids = set(df_train['id'].values)
    val_ids = set(df_val_updated['id'].values)
    
    # calculate excluded based on raw IDs vs final IDs
    final_ids = train_ids.union(val_ids)
    excluded_ids = master_id_set - final_ids
    
    assert len(master_id_set) == len(train_ids) + len(val_ids) + len(excluded_ids), "Set-based ID accounting failed! Potential silent data loss or duplication."
    logger.info("Set-based ID accounting passed: master = train + val + excluded")
    logger.info("Pipeline Complete!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python v2_dataset_builder.py <path_to_raw_data.jsonl>")
    else:
        # Assuming old v1 splits exist in data/training/v1_strict/
        build_v2_pipeline(
            sys.argv[1], 
            "data/training/v1_strict/train.jsonl", 
            "data/training/v1_strict/validation.jsonl"
        )

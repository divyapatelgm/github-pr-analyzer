import os
import json
import logging
from src.deduplicator import Deduplicator
from src.dataset_builder import DatasetBuilder
from src.analytics import Analytics
from src.quality_filter import QualityFilter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StrictPipeline")

def run_strict_pipeline():
    master_data = []
    processed_file = "data/processed/master_dataset_v1.jsonl"
    
    logger.info(f"Loading data from {processed_file}...")
    if os.path.exists(processed_file):
        try:
            with open(processed_file, "r") as f:
                for line in f:
                    if line.strip():
                        master_data.append(json.loads(line))
            logger.info(f"Loaded {len(master_data)} records.")
        except Exception as e:
            logger.error(f"Could not load existing dataset: {e}")
            return
            
    if not master_data:
        logger.warning("No data found to process.")
        return
        
    initial_count = len(master_data)
    
    logger.info("Running strict quality filtering...")
    filterer = QualityFilter(max_diff_length=5000, max_comment_length=2000)
    master_data = filterer.filter(master_data)
    post_filter_count = len(master_data)
    
    logger.info("Running strict deduplication (Fuzzy LSH)...")
    deduper = Deduplicator(threshold=0.85)
    master_data = deduper.deduplicate(master_data)
    post_dedup_count = len(master_data)
    
    logger.info("\n=============================================")
    logger.info("      STRICT PIPELINE DROP-RATE REPORT       ")
    logger.info("=============================================")
    logger.info(f"Initial Records (from basic scraper): {initial_count}")
    logger.info("--- Quality Filtering Drops ---")
    for reason, count in filterer.drop_stats.items():
        if count > 0:
            logger.info(f"  - {reason}: {count}")
    logger.info(f"Records after Quality Filter: {post_filter_count}")
    logger.info("--- Deduplication Drops ---")
    logger.info(f"  - Near-Duplicates / Exact Duplicates: {post_filter_count - post_dedup_count}")
    logger.info(f"Final Strict Production Records: {post_dedup_count}")
    logger.info("=============================================\n")
    
    logger.info("Running analytics...")
    analytics = Analytics()
    analytics.report(master_data)
    
    # Save the strict data splits in a different directory to avoid conflicts
    output_dir = "data/training/v1_strict"
    logger.info(f"Building dataset splits in {output_dir}...")
    builder = DatasetBuilder(output_dir)
    builder.build(master_data)
    
    logger.info("Strict pipeline complete!")

if __name__ == "__main__":
    run_strict_pipeline()

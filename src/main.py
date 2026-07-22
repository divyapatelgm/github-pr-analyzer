import os
import json
import subprocess
from src.github_client import client
from src.repository_scraper import RepositoryScraper
from src.review_extractor import ReviewExtractor
from src.quality_filter import QualityFilter
from src.deduplicator import Deduplicator
from src.metadata_enricher import MetadataEnricher
from src.validator import Validator
from src.dataset_builder import DatasetBuilder
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Pipeline")

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def run_pipeline():
    config = load_config()
    repos = config['scraping']['target_repos']
    
    scraper = RepositoryScraper(repos, max_prs=config['scraping']['max_prs_per_repo'])
    extractor = ReviewExtractor()
    enricher = MetadataEnricher(anonymize=config.get('anonymize_reviewers', True))
    validator = Validator()
    filterer = QualityFilter(min_length=config['filtering']['min_comment_length'], blocklist=config['filtering']['blocklist'])
    deduper = Deduplicator()
    
    os.makedirs("data/processed", exist_ok=True)
    master_data = []
    
    processed_file = "data/processed/master_dataset_v1.jsonl"
    if os.path.exists(processed_file):
        try:
            with open(processed_file, "r") as f:
                for line in f:
                    if line.strip():
                        master_data.append(json.loads(line))
            logger.info(f"Loaded existing dataset with {len(master_data)} records. Resuming...")
        except Exception as e:
            logger.error(f"Could not load existing dataset: {e}")
            
    completed_repos = set(r.get('repo_name') for r in master_data if r.get('repo_name'))
    
    for repo in repos:
        if repo in completed_repos:
            logger.info(f"Skipping {repo} - already found in dataset.")
            continue
            
        try:
            logger.info(f"--- Starting processing for {repo} ---")
            raw_repo_data = []
            prs = scraper.fetch_prs(repo)
            for pr in prs:
                try:
                    pr_num = pr['number']
                    diff = scraper.fetch_pr_diff(repo, pr_num)
                    # We catch exceptions for comments internally or bypass errors here
                    try:
                        comments = scraper.fetch_review_comments(repo, pr_num)
                    except Exception as e:
                        logger.error(f"Error fetching comments for PR {pr_num} in {repo}: {e}")
                        comments = []
                        
                    raw_repo_data.append({
                        "repo_name": repo,
                        "pr_number": pr_num,
                        "diff": diff,
                        "comments": comments,
                        "pr_url": pr['html_url']
                    })
                except Exception as e:
                    logger.error(f"Error processing PR {pr['number']} in {repo}: {e}")
            
            # Process this repo's data
            extracted = extractor.extract_reviews(raw_repo_data)
            enriched = enricher.enrich(extracted)
            validated = validator.validate(enriched)
            filtered = filterer.filter(validated)
            
            # Add to master
            master_data.extend(filtered)
            
            # Save checkpoint immediately
            with open("data/processed/master_dataset_v1.jsonl", "w") as f:
                for r in master_data:
                    f.write(json.dumps(r) + '\n')
                    
            logger.info(f"Checkpoint saved! Accumulated {len(master_data)} clean records so far.")
            
        except Exception as e:
            logger.error(f"Failed processing repository {repo}: {e}")
            
    logger.info("Scraping finished. Running final deduplication across all repos.")
    master_data = deduper.deduplicate(master_data)
    
    with open("data/processed/master_dataset_v1.jsonl", "w") as f:
        for r in master_data:
            f.write(json.dumps(r) + '\n')
            
    from src.analytics import Analytics
    analytics = Analytics()
    analytics.report(master_data)
            
    logger.info("Building dataset splits...")
    builder = DatasetBuilder("data/training/v1")
    builder.build(master_data)
    logger.info("Pipeline complete.")

if __name__ == "__main__":
    run_pipeline()

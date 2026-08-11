import os
import json
import subprocess
from src.github_client import client
from src.repository_scraper import RepositoryScraper
from src.review_extractor import ReviewExtractor
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
    
    os.makedirs("data/processed", exist_ok=True)
    master_data = []
    
    processed_file = "data/processed/master_dataset_v1.jsonl"
    if os.path.exists(processed_file):
        logger.info(f"Existing dataset found at {processed_file}. New records will be appended.")
            
    completed_repos = set()
    if os.path.exists("data/processed/completed_repos.txt"):
        with open("data/processed/completed_repos.txt", "r") as f:
            completed_repos = set(f.read().splitlines())

    for repo in repos:
        if repo in completed_repos:
            logger.info(f"Skipping {repo} - completely finished in a previous run.")
            continue
            
        try:
            logger.info(f"--- Starting processing for {repo} ---")
            raw_repo_data = []
            prs = scraper.fetch_prs(repo)
            for pr in prs:
                try:
                    pr_num = pr['number']
                    # We catch exceptions for comments internally or bypass errors here
                    try:
                        comments = scraper.fetch_review_comments(repo, pr_num)
                    except Exception as e:
                        logger.error(f"Error fetching comments for PR {pr_num} in {repo}: {e}")
                        comments = []
                        
                    raw_repo_data.append({
                        "repo_name": repo,
                        "pr_number": pr_num,
                        "diff": "",
                        "comments": comments,
                        "pr_url": pr['html_url']
                    })
                except Exception as e:
                    logger.error(f"Error processing PR {pr['number']} in {repo}: {e}")
            
            # Process this repo's data (pure extraction only)
            extracted = extractor.extract_reviews(raw_repo_data)
            
            # Add to master
            master_data.extend(extracted)
            
            # Save checkpoint immediately (append mode) with raw nested schema
            with open("data/processed/master_dataset_v1.jsonl", "a", encoding="utf-8") as f:
                for r in extracted:
                    f.write(json.dumps(r) + '\n')
            
            # Log as completed so it can be resumed safely
            with open("data/processed/completed_repos.txt", "a") as f:
                f.write(repo + '\n')
            
            logger.info(f"Checkpoint saved! Accumulated {len(master_data)} raw records so far.")
            
        except Exception as e:
            logger.error(f"Failed processing repository {repo}: {e}")
            
    logger.info("Scraping finished. To process the dataset, run: python -m src.v2_dataset_builder data/processed/master_dataset_v1.jsonl data/training/v1_strict/train.jsonl data/training/v1_strict/validation.jsonl")

if __name__ == "__main__":
    run_pipeline()

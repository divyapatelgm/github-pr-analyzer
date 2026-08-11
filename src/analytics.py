import logging
import pandas as pd
from typing import List, Dict

class Analytics:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_quality_sample(self, df_final: pd.DataFrame, output_path: str = "quality_inspection_v2.csv"):
        """Extract a 100-sample CSV for A/B/C/D/E manual quality check and bot signature discovery."""
        if len(df_final) == 0:
            self.logger.warning("No data to sample for quality inspection.")
            return
            
        sample_size = min(100, len(df_final))
        # Fixed random seed for reproducibility
        df_sample = df_final.sample(n=sample_size, random_state=42)
        
        # Ensure category and notes columns exist
        df_sample['category'] = ""
        df_sample['notes'] = ""
        
        df_sample.to_csv(output_path, index=False, encoding='utf-8')
        self.logger.info(f"Extracted {sample_size} samples to {output_path} for manual A/B/C/D/E inspection.")
        self.logger.info("NOTE: If any sample is labeled E (bot/artifact) and doesn't match an existing signature, loop back to step 4, add signature, and rerun!")

    def check_internal_duplication(self, df_train: pd.DataFrame):
        """Analyze exact input matches within the training set to see if they are cross-PR or same-PR."""
        if df_train.empty:
            return
            
        # Get duplicate inputs
        input_counts = df_train['input'].value_counts()
        duplicates = input_counts[input_counts > 1].index
        
        if len(duplicates) == 0:
            self.logger.info("Training-Internal Duplication: No duplicate inputs found.")
            return
            
        df_dups = df_train[df_train['input'].isin(duplicates)]
        
        same_pr = 0
        cross_pr = 0
        
        # Group by input
        for name, group in df_dups.groupby('input'):
            # Check how many unique PR identifiers this input spans
            # IDs are repo_name_prNumber-reviewId, so PR id is everything before the dash
            pr_ids = set(group['id'].apply(lambda x: x.rsplit('-', 1)[0]))
            if len(pr_ids) == 1:
                same_pr += len(group)
            else:
                cross_pr += len(group)
                
        self.logger.info("--- Training-Internal Duplication Report ---")
        self.logger.info(f"Total duplicate records: {len(df_dups)} out of {len(df_train)}")
        self.logger.info(f"Same-PR duplication (healthy multi-comment threads): {same_pr} records")
        self.logger.info(f"Cross-PR duplication (redundant boilerplate): {cross_pr} records")
        self.logger.info("--------------------------------------------")

    def report(self, master_data: List[Dict]):
        total = len(master_data)
        langs = {}
        for r in master_data:
            lang = r['file']['programming_language']
            langs[lang] = langs.get(lang, 0) + 1
            
        self.logger.info(f"--- Analytics Report ---")
        self.logger.info(f"Total Records: {total}")
        self.logger.info(f"Language Distribution: {langs}")
        self.logger.info(f"------------------------")

import json
import os
import logging
from typing import List, Dict
from sklearn.model_selection import StratifiedGroupKFold
import pandas as pd

class DatasetBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        os.makedirs(output_dir, exist_ok=True)

    def build(self, master_data: List[Dict]):
        if not master_data:
            self.logger.warning("No data to build dataset.")
            return

        df = pd.DataFrame([{
            'id': f"{r['pull_request']['pr_number']}-{r['review']['review_id']}",
            'repo_name': r['repository']['repo_name'],
            'programming_language': r['file']['programming_language'],
            'input': r['review']['code_diff'],
            'output': r['review']['review_comment'],
            'system_prompt': "You are an expert AI code reviewer. Review the following code diff and provide a constructive review comment."
        } for r in master_data])

        unique_repos = df['repo_name'].nunique()
        if unique_repos < 5:
            self.logger.warning(f"Small Dataset Safeguard triggered: Only {unique_repos} repos found. Held-out split may be unreliable.")

        # Using StratifiedGroupKFold to group by repo_name and stratify by programming_language
        sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
        X = df['input']
        y = df['programming_language']
        groups = df['repo_name']
        
        train_idx, temp_idx = next(sgkf.split(X, y, groups))
        
        df_train = df.iloc[train_idx]
        df_temp = df.iloc[temp_idx]
        
        # Split temp into val and test (roughly 50/50 of the 20% temp)
        if df_temp['repo_name'].nunique() > 1:
            sgkf_temp = StratifiedGroupKFold(n_splits=2, shuffle=True, random_state=42)
            val_idx_rel, test_idx_rel = next(sgkf_temp.split(df_temp['input'], df_temp['programming_language'], df_temp['repo_name']))
            df_val = df_temp.iloc[val_idx_rel]
            df_test = df_temp.iloc[test_idx_rel]
        else:
            mid = len(df_temp) // 2
            df_val = df_temp.iloc[:mid]
            df_test = df_temp.iloc[mid:]

        self._save_jsonl(df_train.to_dict('records'), 'train.jsonl')
        self._save_jsonl(df_val.to_dict('records'), 'validation.jsonl')
        self._save_jsonl(df_test.to_dict('records'), 'test.jsonl')

        self.logger.info(f"Dataset generated: {len(df_train)} train, {len(df_val)} val, {len(df_test)} test")

    def _save_jsonl(self, records: List[Dict], filename: str):
        with open(os.path.join(self.output_dir, filename), 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

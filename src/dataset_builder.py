import json
import os
import logging
from typing import List, Dict, Optional
from sklearn.model_selection import GroupShuffleSplit
import pandas as pd

class DatasetBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        os.makedirs(output_dir, exist_ok=True)

    def build(self, master_data: List[Dict], old_pr_assignments: Optional[Dict[str, str]] = None):
        """
        old_pr_assignments: dict mapping pr_identifier -> 'train' or 'val'.
        This ensures structural group-extension merge strategy without post-hoc leakage checking.
        """
        if not master_data:
            self.logger.warning("No data to build dataset.")
            return

        old_pr_assignments = old_pr_assignments or {}

        # 1. Prepare data with proper PR identifier
        records = []
        for r in master_data:
            repo_name = r.get('repo_name', '')
            # Our flat schema id is "repoName_prNumber-reviewId"
            pr_identifier = r.get('id', '').split('-')[0]
            
            records.append({
                'id': r['id'],
                'pr_identifier': pr_identifier,
                'repo_name': repo_name,
                'programming_language': r['programming_language'],
                'input': r.get('input', ''),
                'output': r.get('output', ''),
                'system_prompt': "You are an expert AI code reviewer. Review the following code diff and provide a constructive review comment."
            })
            
        df = pd.DataFrame(records)

        # 2. Separate into old and new PRs
        df['pre_assigned_split'] = df['pr_identifier'].map(old_pr_assignments)
        
        df_old_train = df[df['pre_assigned_split'] == 'train']
        df_old_val = df[df['pre_assigned_split'] == 'val']
        
        df_new = df[df['pre_assigned_split'].isna()].copy()
        
        df_new_train = pd.DataFrame()
        df_new_val = pd.DataFrame()

        # 3. Split new PRs using GroupShuffleSplit (by pr_identifier)
        if not df_new.empty:
            gss = GroupShuffleSplit(n_splits=1, test_size=0.1, random_state=42)
            train_idx, val_idx = next(gss.split(df_new['input'], groups=df_new['pr_identifier']))
            
            df_new_train = df_new.iloc[train_idx]
            df_new_val = df_new.iloc[val_idx]

        # 4. Combine
        df_train = pd.concat([df_old_train, df_new_train], ignore_index=True)
        df_val = pd.concat([df_old_val, df_new_val], ignore_index=True)
        
        # Drop temporary columns
        for d in [df_train, df_val]:
            if 'pr_identifier' in d.columns:
                d.drop(columns=['pr_identifier', 'pre_assigned_split'], inplace=True, errors='ignore')

        # 5. Save outputs
        self._save_jsonl(df_train.to_dict('records'), 'train.jsonl')
        self._save_jsonl(df_val.to_dict('records'), 'validation.jsonl')
        
        df_train.to_csv(os.path.join(self.output_dir, 'train.csv'), index=False, encoding='utf-8')
        df_val.to_csv(os.path.join(self.output_dir, 'validation.csv'), index=False, encoding='utf-8')

        self.logger.info(f"Dataset generated: {len(df_train)} train, {len(df_val)} val")
        self.logger.info(f"Old PRs preserved: {len(df_old_train)} train, {len(df_old_val)} val")
        self.logger.info(f"New PRs split: {len(df_new_train)} train, {len(df_new_val)} val")
        
        return df_train, df_val

    def _save_jsonl(self, records: List[Dict], filename: str):
        with open(os.path.join(self.output_dir, filename), 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

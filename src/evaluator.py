import logging
import json
import os
import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime

class Evaluator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def verify_leakage(self, df_train: pd.DataFrame, df_val: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
        """
        Enforce zero-tolerance leakage checks.
        1. PR Overlap: Exactly 0 by construction.
        2. Exact Input Overlap: Any exact input occurrence found across splits must be investigated
           and excluded from validation (kept in master/train).
        Returns: (success, updated_df_val)
        """
        # 1. PR Overlap check
        # Reconstruct PR identifier from ID (format: repo_name_prNumber-reviewId)
        train_prs = set(df_train['id'].apply(lambda x: x.rsplit('-', 1)[0]))
        val_prs = set(df_val['id'].apply(lambda x: x.rsplit('-', 1)[0]))
        
        pr_overlap = train_prs.intersection(val_prs)
        if pr_overlap:
            self.logger.error(f"[LEAKAGE] Found {len(pr_overlap)} PRs overlapping between train and val! Zero tolerance violated.")
            raise ValueError(f"PR Overlap detected: {list(pr_overlap)[:5]}...")
        else:
            self.logger.info("PR Overlap check passed (0 overlapping PRs).")

        # 2. Exact Input Overlap check
        train_inputs = set(df_train['input'].values)
        val_inputs = set(df_val['input'].values)
        
        exact_input_overlap = train_inputs.intersection(val_inputs)
        if exact_input_overlap:
            self.logger.warning(f"[LEAKAGE] Found {len(exact_input_overlap)} exact inputs overlapping. Excluding from validation.")
            # Drop from validation
            initial_val_len = len(df_val)
            df_val = df_val[~df_val['input'].isin(exact_input_overlap)]
            self.logger.info(f"Excluded {initial_val_len - len(df_val)} records from validation due to exact input overlap.")
        else:
            self.logger.info("Exact Input Overlap check passed (0 overlapping inputs).")

        return True, df_val

    def evaluate(self, model_name: str, metrics: dict):
        report_path = "evaluation_report.md"
        with open(report_path, "a") as f:
            f.write(f"\n## Evaluation - {datetime.now().isoformat()}\n")
            f.write(f"- **Model**: {model_name}\n")
            for k, v in metrics.items():
                f.write(f"- **{k}**: {v}\n")
        self.logger.info(f"Appended evaluation to {report_path}")

    def log_experiment(self, experiment_data: dict):
        with open("experiments.jsonl", "a") as f:
            f.write(json.dumps(experiment_data) + "\n")

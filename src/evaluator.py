import logging
import json
import os
from datetime import datetime

class Evaluator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

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

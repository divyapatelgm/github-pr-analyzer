import logging
from typing import List, Dict

class Flattener:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def flatten(self, raw_records: List[Dict]) -> List[Dict]:
        """
        Transforms the raw nested schema into the flat schema expected by all downstream pipeline steps.
        """
        if not raw_records:
            return []

        flattened = []
        for r in raw_records:
            try:
                repo_name = r.get('repository', {}).get('repo_name', '')
                pr_number = str(r.get('pull_request', {}).get('pr_number', ''))
                review_id = str(r.get('review', {}).get('review_id', ''))
                
                # PR ID parsing downstream expects repo_name_prNumber-reviewId
                flat_id = f"{repo_name}_{pr_number}-{review_id}"
                
                flat_record = {
                    'id': flat_id,
                    'repo_name': repo_name,
                    'programming_language': r.get('file', {}).get('programming_language', ''),
                    'input': r.get('review', {}).get('code_diff', ''),
                    'output': r.get('review', {}).get('review_comment', ''),
                    'system_prompt': "You are an expert AI code reviewer. Review the following code diff and provide a constructive review comment."
                }
                flattened.append(flat_record)
            except Exception as e:
                self.logger.error(f"Error flattening record: {e}")
                
        self.logger.info(f"Flattened {len(flattened)} records.")
        return flattened

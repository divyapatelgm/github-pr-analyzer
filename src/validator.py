from typing import List, Dict
import logging

class Validator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate(self, records: List[Dict]) -> List[Dict]:
        valid = []
        seen_ids = set()
        
        for record in records:
            repo_name = record['repository']['repo_name']
            pr_number = record['pull_request']['pr_number']
            code_diff = record['review']['code_diff']
            review_comment = record['review']['review_comment']
            review_id = record['review']['review_id']
            language = record['file']['programming_language']
            
            if not all([repo_name, pr_number, code_diff, review_comment]):
                self.logger.warning(f"Validation failed: missing required field for review_id {review_id}")
                continue
                
            if review_id in seen_ids:
                self.logger.warning(f"Validation failed: duplicate review_id {review_id}")
                continue
                
            if language == "unknown":
                self.logger.warning(f"Validation failed: unknown language for review_id {review_id}")
                continue
                
            seen_ids.add(review_id)
            valid.append(record)
            
        self.logger.info(f"Validator: kept {len(valid)} out of {len(records)} records")
        return valid

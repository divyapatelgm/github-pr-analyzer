import logging
from typing import List, Dict

class Validator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.expected_keys = {'id', 'repo_name', 'programming_language', 'input', 'output', 'system_prompt'}

    def validate_schema(self, first_record: Dict) -> None:
        """Fail loudly if the schema deviates from the expected flat structure."""
        if not first_record:
            raise ValueError("Cannot validate schema on empty dataset.")
            
        record_keys = set(first_record.keys())
        missing_keys = self.expected_keys - record_keys
        if missing_keys:
            raise ValueError(f"Schema mismatch! Missing required keys: {missing_keys}")

    def validate(self, records: List[Dict]) -> List[Dict]:
        if not records:
            return []
            
        # Strict schema verification on the first record before looping
        self.validate_schema(records[0])
        
        valid = []
        seen_ids = set()
        
        for record in records:
            repo_name = record.get('repo_name')
            pr_id = record.get('id')
            code_diff = record.get('input')
            review_comment = record.get('output')
            language = record.get('programming_language')
            
            if not all([repo_name, pr_id, code_diff, review_comment]):
                self.logger.warning(f"Validation failed: missing required field for record {pr_id}")
                continue
                
            if pr_id in seen_ids:
                self.logger.warning(f"Validation failed: duplicate id {pr_id}")
                continue
                
            if language == "unknown":
                self.logger.warning(f"Validation failed: unknown language for id {pr_id}")
                continue
                
            seen_ids.add(pr_id)
            valid.append(record)
            
        self.logger.info(f"Validator: kept {len(valid)} out of {len(records)} records")
        return valid

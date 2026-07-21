from typing import List, Dict
import logging

class Deduplicator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        
        for record in records:
            comment = record['review']['review_comment']
            diff = record['review']['code_diff']
            pr_num = record['pull_request']['pr_number']
            
            key = f"{comment}|{diff}|{pr_num}"
            if key not in seen:
                seen.add(key)
                unique.append(record)
                
        self.logger.info(f"Deduplicator: removed {len(records) - len(unique)} duplicates")
        return unique

from typing import List, Dict
import logging

class QualityFilter:
    def __init__(self, min_length: int = 3, blocklist: List[str] = None):
        self.min_length = min_length
        self.blocklist = [b.lower() for b in (blocklist or [])]
        self.logger = logging.getLogger(self.__class__.__name__)

    def filter(self, records: List[Dict]) -> List[Dict]:
        filtered = []
        for record in records:
            comment = record['review']['review_comment']
            if not comment or not comment.strip():
                continue
                
            words = comment.split()
            if len(words) < self.min_length:
                continue
                
            comment_lower = comment.lower()
            if any(b in comment_lower for b in self.blocklist):
                continue
                
            if not record['review']['code_diff']:
                continue
                
            filtered.append(record)
        
        self.logger.info(f"Quality filter: kept {len(filtered)} out of {len(records)} records")
        return filtered

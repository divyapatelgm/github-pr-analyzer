from typing import List, Dict, Tuple
import logging

class QualityFilter:
    def __init__(self, min_length: int = 3, blocklist: List[str] = None, max_diff_length: int = 5000, max_comment_length: int = 2000):
        self.min_length = min_length
        self.max_diff_length = max_diff_length
        self.max_comment_length = max_comment_length
        self.blocklist = [b.lower() for b in (blocklist or [])]
        self.logger = logging.getLogger(self.__class__.__name__)
        self.drop_stats = {
            "empty_comment": 0,
            "too_short": 0,
            "too_long_comment": 0,
            "blocklist_match": 0,
            "empty_diff": 0,
            "too_long_diff": 0,
            "bot_comment": 0
        }

    def filter(self, records: List[Dict]) -> List[Dict]:
        filtered = []
        for record in records:
            comment = record['review']['review_comment']
            
            if record['review'].get('is_bot', False):
                self.drop_stats["bot_comment"] += 1
                continue
                
            if not comment or not comment.strip():
                self.drop_stats["empty_comment"] += 1
                continue
                
            if len(comment) > self.max_comment_length:
                self.drop_stats["too_long_comment"] += 1
                continue
                
            words = comment.split()
            if len(words) < self.min_length:
                self.drop_stats["too_short"] += 1
                continue
                
            comment_lower = comment.lower()
            if any(b in comment_lower for b in self.blocklist):
                self.drop_stats["blocklist_match"] += 1
                continue
                
            code_diff = record['review']['code_diff']
            if not code_diff:
                self.drop_stats["empty_diff"] += 1
                continue
                
            if len(code_diff) > self.max_diff_length:
                self.drop_stats["too_long_diff"] += 1
                continue
                
            filtered.append(record)
        
        self.logger.info(f"Quality filter: kept {len(filtered)} out of {len(records)} records")
        self.logger.info(f"Drop stats: {self.drop_stats}")
        return filtered

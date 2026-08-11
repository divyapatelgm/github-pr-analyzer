from typing import List, Dict
import logging
from datasketch import MinHash, MinHashLSH

class Deduplicator:
    def __init__(self, threshold: float = 0.85, num_perm: int = 128):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.threshold = threshold
        self.num_perm = num_perm

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        unique = []
        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        
        duplicates_removed = 0
        seen_exact = set()
        
        self.logger.info(f"Starting deduplication for {len(records)} records with threshold {self.threshold}...")
        
        for idx, record in enumerate(records):
            comment = record['review']['review_comment']
            diff = record['review']['code_diff']
            pr_num = record['pull_request']['pr_number']
            
            key = f"{comment}|{diff}|{pr_num}"
            if key in seen_exact:
                duplicates_removed += 1
                continue
            seen_exact.add(key)
            
            content = f"{comment} {diff}"
            tokens = set(content.lower().split())
            
            m = MinHash(num_perm=self.num_perm)
            for d in tokens:
                m.update(d.encode('utf8'))
                
            result = lsh.query(m)
            if not result:
                lsh.insert(str(idx), m)
                unique.append(record)
            else:
                duplicates_removed += 1
                
        self.logger.info(f"Deduplicator: removed {duplicates_removed} duplicates")
        self.logger.info(f"Deduplicator drop stats: {{'duplicates_removed': {duplicates_removed}}}")
        return unique

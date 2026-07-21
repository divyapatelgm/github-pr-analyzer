from typing import List, Dict
import hashlib
import os

LANGUAGE_MAP = {
    "py": "python", "js": "javascript", "ts": "typescript", "java": "java", 
    "go": "go", "rs": "rust", "cpp": "cpp", "c": "c", "cs": "csharp",
    "rb": "ruby", "php": "php", "swift": "swift", "kt": "kotlin",
    "yaml": "yaml", "yml": "yaml", "md": "markdown", "json": "json",
    "toml": "toml", "dockerfile": "dockerfile", "ini": "ini", "cfg": "ini",
    "sh": "shell", "bash": "shell", "html": "html", "css": "css"
}

class MetadataEnricher:
    def __init__(self, anonymize: bool = True):
        self.anonymize = anonymize

    def enrich(self, records: List[Dict]) -> List[Dict]:
        for record in records:
            path = record['file']['file_path']
            ext = path.split('.')[-1].lower() if '.' in path else path.split('/')[-1].lower()
            
            lang = LANGUAGE_MAP.get(ext, "unknown")
            record['file']['file_extension'] = ext
            record['file']['programming_language'] = lang
            
            if self.anonymize and record['review']['reviewer']:
                record['review']['reviewer'] = hashlib.sha256(record['review']['reviewer'].encode()).hexdigest()[:8]
                
            comment_len = len(record['review']['review_comment'].split())
            record['metadata']['token_count'] = str(comment_len)
            record['metadata']['quality_score'] = "high" if comment_len > 10 else "medium"
            
        return records

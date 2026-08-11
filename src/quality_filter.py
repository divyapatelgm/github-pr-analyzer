import re
from typing import List, Dict
import logging
import numpy as np
from collections import Counter
from transformers import AutoTokenizer

class QualityFilter:
    def __init__(self, min_length: int = 3):
        self.min_length = min_length
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load the Qwen tokenizer for accurate token length calculation
        # Uses apply_chat_template under the hood implicitly via tokenization if needed, 
        # but standard encode is typically close enough or we can use the chat template directly.
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True)
        except Exception as e:
            self.logger.warning(f"Failed to load Qwen tokenizer, falling back to basic split. Error: {e}")
            self.tokenizer = None
            
        self.blocklist = [
            r'codecov', r'sonarcloud', r'dependabot', r'linter', r'automatically generated',
            r'auto-resolved', r'codereviewagent', r'greptile', r'pullpo\.io',
            r'(?<!copilot apply)copilot', r'copilot/copilot app', 
            r'🧩 analysis chain', r'web query:', r'script executed:', r'cubic:', r'<!--.*-->'
        ]
        
        self.drop_stats = {
            "empty_comment": 0,
            "too_short": 0,
            "too_long_context": 0,
            "blocklist_match": 0,
            "empty_diff": 0,
            "bot_comment": 0,
            "image_only": 0
        }

    def _is_image_only(self, text: str) -> bool:
        """Strip image tags and check if the remaining text is exactly 0 words."""
        # Strip markdown images: ![alt](url)
        no_md_imgs = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # Strip HTML images: <img ... />
        no_html_imgs = re.sub(r'<img[^>]*>', '', no_md_imgs)
        
        words = no_html_imgs.split()
        return len(words) == 0

    def _get_token_length(self, text: str) -> int:
        if self.tokenizer:
            # The chat template adds ~13 tokens, we simulate it here by adding 13.
            return len(self.tokenizer.encode(text)) + 13
        return len(text.split()) # Fallback

    def filter(self, records: List[Dict]) -> List[Dict]:
        if not records:
            return []

        # 1. Hardcode context length cutoff to 4096 to match V1 and T4 GPU constraints
        context_length_cutoff = 4096
        self.logger.info(f"Using fixed context length cutoff: {context_length_cutoff} tokens")

        filtered = []
        normalized_outputs = []
        
        for record in records:
            comment = record.get('output', '')
            code_diff = record.get('input', '')
            
            # Since is_bot was nested in 'review' but isn't explicitly in the flat schema,
            # we rely entirely on the regex bot signatures to catch bots in the comment text.
            if not comment or not comment.strip():
                self.drop_stats["empty_comment"] += 1
                continue
                
            if self._is_image_only(comment):
                self.drop_stats["image_only"] += 1
                continue
                
            if not code_diff:
                self.drop_stats["empty_diff"] += 1
                continue
                
            total_len = self._get_token_length(code_diff) + self._get_token_length(comment)
            if total_len > context_length_cutoff:
                self.drop_stats["too_long_context"] += 1
                continue
                
            words = comment.split()
            if len(words) < self.min_length:
                self.drop_stats["too_short"] += 1
                continue
                
            comment_lower = comment.lower()
            if any(re.search(b, comment_lower) for b in self.blocklist):
                self.drop_stats["blocklist_match"] += 1
                continue
                
            filtered.append(record)
            
            # Normalize for repetition analysis: remove punctuation, lowercase, strip whitespace
            norm_comment = re.sub(r'[^\w\s]', '', comment_lower).strip()
            normalized_outputs.append(norm_comment)
            
        # Repetition Analysis Trigger
        total_kept = len(filtered)
        if total_kept > 0:
            counter = Counter(normalized_outputs)
            top_50 = counter.most_common(50)
            top_50_count = sum(count for _, count in top_50)
            
            repetition_ratio = top_50_count / total_kept
            self.logger.info(f"Top 50 normalized outputs account for {repetition_ratio:.2%} of the dataset.")
            
            if repetition_ratio > 0.05:
                self.logger.warning("[ESCALATION] Top 50 normalized outputs exceed 5% of the dataset. Semantic/embedding-based deduplication is required.")

        self.logger.info(f"Quality filter: kept {len(filtered)} out of {len(records)} records")
        self.logger.info(f"Drop stats: {self.drop_stats}")
        return filtered

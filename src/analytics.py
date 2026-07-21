import logging
from typing import List, Dict

class Analytics:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def report(self, master_data: List[Dict]):
        total = len(master_data)
        langs = {}
        for r in master_data:
            lang = r['file']['programming_language']
            langs[lang] = langs.get(lang, 0) + 1
            
        self.logger.info(f"--- Analytics Report ---")
        self.logger.info(f"Total Records: {total}")
        self.logger.info(f"Language Distribution: {langs}")
        self.logger.info(f"------------------------")

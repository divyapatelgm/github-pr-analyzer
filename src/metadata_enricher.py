import os
import json
import time
import requests
import logging
from typing import List, Dict
from collections import defaultdict

class MetadataEnricher:
    def __init__(self, cache_file: str = "data/processed/license_cache.json"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache_file = cache_file
        self.license_cache = {}
        self.github_token = os.environ.get("GITHUB_TOKEN")
        
        self.copyleft_licenses = ['gpl', 'agpl', 'lgpl']
        
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                loaded_cache = json.load(f)
                # Migrate old string cache entries to the new dictionary format
                for k, v in loaded_cache.items():
                    if isinstance(v, str):
                        self.license_cache[k] = {'key': v, 'download_url': None}
                    else:
                        self.license_cache[k] = v

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.license_cache, f, indent=2)

    def _fetch_license_info(self, repo_name: str) -> Dict:
        if repo_name in self.license_cache:
            return self.license_cache[repo_name]
            
        url = f"https://api.github.com/repos/{repo_name}/license"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
            
        lic_info = {'key': 'unknown', 'download_url': None}
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                lic_info['key'] = data.get('license', {}).get('key', 'unknown')
                lic_info['download_url'] = data.get('download_url')
            elif resp.status_code == 404:
                lic_info['key'] = 'no-license-file'
            elif resp.status_code == 403 and 'rate limit' in resp.text.lower():
                self.logger.warning("GitHub API Rate limit exceeded while fetching licenses. Pausing for 60s...")
                time.sleep(60)
                return self._fetch_license_info(repo_name)
                
            self.license_cache[repo_name] = lic_info
            self._save_cache()
            return lic_info
        except Exception as e:
            self.logger.error(f"Error fetching license for {repo_name}: {e}")
            return lic_info

    def enrich_and_report_provenance(self, records: List[Dict]):
        # Calculate record-weighted impact
        repo_record_counts = defaultdict(int)
        for r in records:
            repo_record_counts[r['repo_name']] += 1
            
        repos = list(repo_record_counts.keys())
        self.logger.info(f"Fetching licenses for {len(repos)} repositories...")
        
        copyleft_flags = []
        no_license_flags = []
        noassertion_repos = []
        
        for repo in repos:
            lic_info = self._fetch_license_info(repo)
            lic_key = lic_info['key']
            
            if lic_key == 'no-license-file':
                no_license_flags.append(repo)
            elif lic_key == 'other': # GitHub uses 'other' for NOASSERTION
                noassertion_repos.append(repo)
            elif any(c in lic_key.lower() for c in self.copyleft_licenses):
                copyleft_flags.append(f"{repo} ({lic_key})")
                
        self.logger.info("--- Provenance & License Report ---")
        self.logger.info(f"Total Repositories: {len(repos)}")
        
        if no_license_flags:
            impact = sum(repo_record_counts[r] for r in no_license_flags)
            self.logger.warning(f"[FLAG] Found {len(no_license_flags)} repos with no detectable license file (Impact: {impact:,} records).")
        
        if copyleft_flags:
            impact = sum(repo_record_counts[r.split(' ')[0]] for r in copyleft_flags)
            self.logger.warning(f"[FLAG] Found {len(copyleft_flags)} repos with Copyleft licenses (Impact: {impact:,} records).")
            
        if noassertion_repos:
            # Sort by record impact descending
            noassertion_repos.sort(key=lambda r: repo_record_counts[r], reverse=True)
            impact = sum(repo_record_counts[r] for r in noassertion_repos)
            self.logger.warning(f"[FLAG] Found {len(noassertion_repos)} repos with NOASSERTION/'other' licenses (Impact: {impact:,} records).")
            self.logger.warning("Top 5 NOASSERTION repos by record impact (MANUAL REVIEW REQUIRED):")
            for repo in noassertion_repos[:5]:
                count = repo_record_counts[repo]
                dl_url = self.license_cache[repo].get('download_url')
                self.logger.warning(f" - {repo} ({count:,} records) | Raw License URL: {dl_url}")
                
        with open("provenance_v2.json", "w", encoding='utf-8') as f:
            json.dump({
                "total_repos": len(repos),
                "repo_record_counts": repo_record_counts,
                "no_license": no_license_flags,
                "copyleft": copyleft_flags,
                "noassertion_repos_by_impact": sorted(noassertion_repos, key=lambda r: repo_record_counts[r], reverse=True),
                "all_licenses": self.license_cache
            }, f, indent=2)

    def enrich(self, records: List[Dict]) -> List[Dict]:
        # Since flattening happens at Step 0, all necessary flat fields are already present.
        # This function acts as a pass-through to satisfy the pipeline structure.
        return records

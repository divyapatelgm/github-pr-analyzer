from src.github_client import client
import logging
from typing import List, Dict, Any

class RepositoryScraper:
    def __init__(self, target_repos: List[str], max_prs: int = 100):
        self.target_repos = target_repos
        self.max_prs = max_prs
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_prs(self, repo: str) -> List[Dict]:
        self.logger.info(f"Fetching PRs for {repo}")
        endpoint = f"repos/{repo}/pulls"
        params = {"state": "closed"}
        return client.get_paginated(endpoint, params=params, max_pages=max(1, self.max_prs // 100))

    def fetch_review_comments(self, repo: str, pr_number: int) -> List[Dict]:
        endpoint = f"repos/{repo}/pulls/{pr_number}/comments"
        return client.get_paginated(endpoint)



    def fetch_all(self):
        raw_data = []
        for repo in self.target_repos:
            prs = self.fetch_prs(repo)
            for pr in prs:
                pr_number = pr['number']
                comments = self.fetch_review_comments(repo, pr_number)
                
                raw_data.append({
                    "repo_name": repo,
                    "pr_number": pr_number,
                    "diff": "",

                    "comments": comments,
                    "pr_url": pr['html_url']
                })
        return raw_data

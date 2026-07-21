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

    def fetch_pr_diff(self, repo: str, pr_number: int) -> str:
        import requests
        endpoint = f"repos/{repo}/pulls/{pr_number}"
        try:
            response = client.session.get(f"{client.base_url}/{endpoint}", headers={"Accept": "application/vnd.github.v3.diff"})
            client._handle_rate_limit(response)
            if response.status_code == 406:
                self.logger.warning(f"Diff not acceptable (406) for PR {pr_number} in {repo}. Skipping.")
                return ""
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching diff for PR {pr_number} in {repo}: {e}")
            return ""

    def fetch_all(self):
        raw_data = []
        for repo in self.target_repos:
            prs = self.fetch_prs(repo)
            for pr in prs:
                pr_number = pr['number']
                diff = self.fetch_pr_diff(repo, pr_number)
                comments = self.fetch_review_comments(repo, pr_number)
                
                raw_data.append({
                    "repo_name": repo,
                    "pr_number": pr_number,
                    "diff": diff,
                    "comments": comments,
                    "pr_url": pr['html_url']
                })
        return raw_data
